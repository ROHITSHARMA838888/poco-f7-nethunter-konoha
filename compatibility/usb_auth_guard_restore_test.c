/* Host-only inode restoration integration tests; never touches sysfs. */
#define main guard_cli_main
#include "usb_auth_guard.c"
#undef main
#include <assert.h>

static void expect_mode(int fd, mode_t mode) {
    struct stat s;
    for (int i = 0; i < 200; i++) {
        assert(!fstat(fd, &s));
        if ((s.st_mode & 07777) == mode) return;
        usleep(10000);
    }
    assert(!"independent restore timed out");
}
int main(void) {
    for (int i = 0; i < MAX_HUBS; i++) guards[i].fd = guards[i].life = -1;
    signal(SIGCHLD, SIG_IGN);
    char path[] = "/tmp/onyx-usb-inode-XXXXXX";
    int fd = mkstemp(path);
    assert(fd >= 0 && !fchmod(fd, 0640));
    int life = restore_child(fd, 0640, 0440);
    assert(life >= 0 && !fchmod(fd, 0440));
    close(life);
    expect_mode(fd, 0640);
    puts("PASS: pipe EOF restores original permissions");

    life = restore_child(fd, 0640, 0440);
    assert(life >= 0 && !fchmod(fd, 0440));
    char oldpath[PATH_MAX];
    snprintf(oldpath, sizeof(oldpath), "%s.old", path);
    assert(!rename(path, oldpath));
    int replacement = open(path, O_CREAT | O_EXCL | O_RDWR, 0600);
    assert(replacement >= 0 && !fchmod(replacement, 0600));
    close(life);
    expect_mode(fd, 0640);
    expect_mode(replacement, 0600);
    puts("PASS: restore affects original inode, not replacement path");

    int notify[2];
    assert(!pipe(notify));
    pid_t worker = fork();
    assert(worker >= 0);
    if (!worker) {
        close(notify[0]);
        int token = restore_child(fd, 0640, 0440);
        assert(token >= 0 && !fchmod(fd, 0440));
        assert(write(notify[1], "x", 1) == 1);
        for (;;) pause();
    }
    close(notify[1]);
    char byte;
    assert(read(notify[0], &byte, 1) == 1);
    assert(!kill(worker, SIGKILL));
    expect_mode(fd, 0640);
    puts("PASS: worker SIGKILL triggers independent restore");
    close(notify[0]); close(fd); close(replacement);
    assert(!unlink(path) && !unlink(oldpath));
    return 0;
}

