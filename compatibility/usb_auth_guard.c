#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <linux/netlink.h>
#include <poll.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

/* No writes to USB authorization values, ROM, properties or SELinux policy.
 * Restrict only the parent hub's authorization mode while one of two exact
 * known adapters is present. The original open inode is retained for restore.
 * A child with a private pipe restores modes if the parent exits or crashes.
 */
#define MAX_HUBS 8
#define STATE "/data/adb/onyx-drivers-40863319425"
struct guard {
    int fd, life;
    mode_t before, guarded;
    dev_t dev;
    ino_t ino;
    bool seen;
    char path[PATH_MAX];
};
static struct guard guards[MAX_HUBS];
static volatile sig_atomic_t alive = 1;
static int netfd = -1, lockfd = -1;
static void stop(int sig) { (void)sig; alive = 0; }
static double now(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts)) return 0;
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}
static bool read_value(const char *path, unsigned *value) {
    char buf[64];
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) return false;
    ssize_t n = read(fd, buf, sizeof(buf) - 1);
    close(fd);
    if (n <= 0) return false;
    buf[n] = 0;
    return sscanf(buf, "%x", value) == 1;
}
static void restore(int fd, mode_t before, mode_t guarded) {
    struct stat s;
    /* Do not overwrite a permission choice made by another actor. */
    if (!fstat(fd, &s) && (s.st_mode & 07777) == guarded) {
        if (fchmod(fd, before) && errno != ENOENT && errno != ENODEV)
            fprintf(stderr, "RESTORE_ERROR:%s\n", strerror(errno));
    }
}
static void release(struct guard *g) {
    if (g->fd < 0) return;
    restore(g->fd, g->before, g->guarded);
    printf("RESTORED:%s mode=%04o\n", g->path, (unsigned)g->before);
    close(g->fd);
    close(g->life); /* EOF also releases the independent inode restore child. */
    g->fd = g->life = -1;
}
static int restore_child(int fd, mode_t before, mode_t guarded) {
    int pipefd[2];
    if (pipe2(pipefd, O_CLOEXEC)) return -1;
    pid_t child = fork();
    if (child < 0) { close(pipefd[0]); close(pipefd[1]); return -1; }
    if (!child) {
        close(pipefd[1]);
        if (netfd >= 0) close(netfd);
        if (lockfd >= 0) close(lockfd);
        for (int i = 0; i < MAX_HUBS; i++) {
            if (guards[i].life >= 0) close(guards[i].life);
            if (guards[i].fd >= 0 && guards[i].fd != fd) close(guards[i].fd);
        }
        char byte;
        while (alive) {
            ssize_t n = read(pipefd[0], &byte, 1);
            if (!n || (n < 0 && errno != EINTR)) break;
        }
        restore(fd, before, guarded);
        close(fd);
        close(pipefd[0]);
        _exit(0);
    }
    close(pipefd[0]);
    return pipefd[1];
}
static void protect(const char *path) {
    struct stat s;
    if (stat(path, &s)) return;
    for (int i = 0; i < MAX_HUBS; i++) {
        struct guard *g = &guards[i];
        if (g->fd >= 0 && g->dev == s.st_dev && g->ino == s.st_ino) {
            g->seen = true;
            if ((s.st_mode & 07777) == g->before && fchmod(g->fd, g->guarded))
                fprintf(stderr, "REAPPLY_ERROR:%s\n", strerror(errno));
            return;
        }
    }
    int slot;
    for (slot = 0; slot < MAX_HUBS && guards[slot].fd >= 0; slot++) {}
    if (slot == MAX_HUBS) return;
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0 || fstat(fd, &s)) { if (fd >= 0) close(fd); return; }
    char value;
    if (pread(fd, &value, 1, 0) != 1 || value != '1') { close(fd); return; }
    mode_t before = s.st_mode & 07777, guarded = before & ~(mode_t)0222;
    if (before == guarded) { close(fd); return; }
    int life = restore_child(fd, before, guarded);
    if (life < 0) { close(fd); return; }
    if (fchmod(fd, guarded) || pread(fd, &value, 1, 0) != 1 || value != '1') {
        restore(fd, before, guarded);
        close(fd); close(life); return;
    }
    struct guard *g = &guards[slot];
    g->fd = fd; g->life = life; g->seen = true;
    g->dev = s.st_dev; g->ino = s.st_ino;
    g->before = before; g->guarded = guarded;
    snprintf(g->path, sizeof(g->path), "%s", path);
    printf("PROTECTED:%s mode=%04o->%04o\n", path, (unsigned)before, (unsigned)guarded);
}
static unsigned rescan(void) {
    for (int i = 0; i < MAX_HUBS; i++) guards[i].seen = false;
    DIR *dir = opendir("/sys/bus/usb/devices");
    if (!dir) return 0;
    struct dirent *entry;
    while ((entry = readdir(dir))) {
        if (entry->d_name[0] == '.' || strchr(entry->d_name, ':')) continue;
        char p[PATH_MAX], q[PATH_MAX], real[PATH_MAX];
        unsigned vid, pid;
        int n = snprintf(p, sizeof(p), "/sys/bus/usb/devices/%s/idVendor", entry->d_name);
        if (n < 0 || (size_t)n >= sizeof(p) || !read_value(p, &vid)) continue;
        n = snprintf(p, sizeof(p), "/sys/bus/usb/devices/%s/idProduct", entry->d_name);
        if (n < 0 || (size_t)n >= sizeof(p) || !read_value(p, &pid)) continue;
        if (vid != 0x2357 || (pid != 0x0120 && pid != 0x010c)) continue;
        n = snprintf(q, sizeof(q), "/sys/bus/usb/devices/%s/../authorized", entry->d_name);
        if (n < 0 || (size_t)n >= sizeof(q) || !realpath(q, real)) continue;
        size_t len = strlen(real);
        if (strncmp(real, "/sys/devices/", 13) || !strstr(real, "/usb") ||
            len < 11 || strcmp(real + len - 11, "/authorized")) continue;
        printf("TARGET:%04x:%04x\n", vid, pid);
        protect(real);
    }
    closedir(dir);
    unsigned count = 0;
    for (int i = 0; i < MAX_HUBS; i++) {
        if (guards[i].fd >= 0 && !guards[i].seen) release(&guards[i]);
        if (guards[i].fd >= 0) count++;
    }
    return count;
}
static bool usb_event(const char *buf, size_t len) {
    for (size_t pos = 0; pos < len;) {
        size_t n = strnlen(buf + pos, len - pos);
        if (n == len - pos) break;
        if (!strcmp(buf + pos, "SUBSYSTEM=usb")) return true;
        pos += n + 1;
    }
    return false;
}
int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IOLBF, 0);
    if (argc != 2 || strcmp(argv[1], "--test")) {
        puts("Usage: usb-auth-guard --test (45s maximum after first protected adapter; 2h idle limit)");
        return argc == 2 && !strcmp(argv[1], "--help") ? 0 : 2;
    }
    if (geteuid()) return 1;
    for (int i = 0; i < MAX_HUBS; i++) guards[i].fd = guards[i].life = -1;
    struct sigaction sa = {0}; sa.sa_handler = stop;
    sigaction(SIGTERM, &sa, NULL); sigaction(SIGINT, &sa, NULL);
    struct sigaction child = {0}; child.sa_handler = SIG_IGN;
    sigaction(SIGCHLD, &child, NULL);
    lockfd = open(STATE "/usb-auth-guard.lock", O_CREAT | O_RDWR | O_CLOEXEC, 0600);
    if (lockfd < 0 || flock(lockfd, LOCK_EX | LOCK_NB)) { perror("guard lock"); return 1; }
    netfd = socket(AF_NETLINK, SOCK_DGRAM | SOCK_CLOEXEC | SOCK_NONBLOCK, NETLINK_KOBJECT_UEVENT);
    if (netfd < 0) { perror("uevent socket"); return 1; }
    struct sockaddr_nl address = {.nl_family = AF_NETLINK, .nl_pid = (unsigned)getpid(), .nl_groups = 1};
    if (bind(netfd, (struct sockaddr *)&address, sizeof(address))) { perror("uevent bind"); return 1; }
    double began = now(), active = 0;
    printf("GUARD_TEST_READY pid=%ld\n", (long)getpid());
    unsigned count = rescan();
    while (alive && now() - began < 7200) {
        if (count && !active) active = now();
        if (active && now() - active >= 45) break;
        struct pollfd p = {.fd = netfd, .events = POLLIN};
        int ready = poll(&p, 1, 500);
        if (ready < 0) { if (errno == EINTR) continue; break; }
        if (!ready) continue;
        char buf[16384]; struct sockaddr_nl from; socklen_t fromlen = sizeof(from);
        ssize_t n = recvfrom(netfd, buf, sizeof(buf), MSG_DONTWAIT, (struct sockaddr *)&from, &fromlen);
        if (n > 0 && fromlen >= sizeof(from) && !from.nl_pid && usb_event(buf, (size_t)n))
            count = rescan();
    }
    for (int i = 0; i < MAX_HUBS; i++) release(&guards[i]);
    close(netfd); close(lockfd);
    puts("GUARD_TEST_STOPPED: original inode permissions restored");
    return 0;
}

