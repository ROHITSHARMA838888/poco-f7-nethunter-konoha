#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C
source drivers.lock
mkdir -p external wireless-modules diagnostics
failed=0
expected_release=$(cat kernel/out/include/config/kernel.release)
for driver in rtl8812au rtl8188eus; do
  if [ "$driver" = rtl8812au ]; then
    remote="$RTL8812AU_REPOSITORY"; revision="$RTL8812AU_COMMIT"
  else
    remote="$RTL8188EUS_REPOSITORY"; revision="$RTL8188EUS_COMMIT"
  fi
  git init "external/$driver"
  git -C "external/$driver" remote add origin "$remote"
  git -C "external/$driver" fetch --depth=1 origin "$revision"
  git -C "external/$driver" checkout --detach FETCH_HEAD
  test "$(git -C "external/$driver" rev-parse HEAD)" = "$revision"
  python3 scripts/prepare-driver.py "external/$driver"
  git -C "external/$driver" diff --check
  git -C "external/$driver" diff > "diagnostics/$driver-source-fixes.patch"
  # Keep going within each driver to collect every compiler error in one run.
  if ! make -k -j"$(nproc)" -C kernel O=out ARCH=arm64 LLVM=1 \
      M="$GITHUB_WORKSPACE/external/$driver" \
      CONFIG_88XXAU=m CONFIG_RTL8188EU=m CONFIG_PLATFORM_I386_PC=n \
      USER_EXTRA_CFLAGS="-DCONFIG_LITTLE_ENDIAN -DCONFIG_IOCTL_CFG80211 -DRTW_USE_CFG80211_STA_EVENT" \
      modules 2>&1 | tee "diagnostics/$driver.log"; then
    failed=1
    continue
  fi
  mapfile -t modules < <(find "external/$driver" -name '*.ko' -type f)
  if [ "${#modules[@]}" -eq 0 ]; then
    echo "No kernel module produced for $driver" | tee -a "diagnostics/$driver.log"
    failed=1
    continue
  fi
  for module in "${modules[@]}"; do
    if ! llvm-readelf -h "$module" | grep -q 'Machine:.*AArch64'; then
      echo "Wrong module architecture: $module"
      failed=1
      continue
    fi
    vermagic=$(modinfo -F vermagic "$module")
    if [ "${vermagic%% *}" != "$expected_release" ]; then
      echo "Kernel release mismatch for $module: $vermagic"
      failed=1
      continue
    fi
    modinfo "$module" > "diagnostics/$(basename "$module").modinfo.txt"
    cp "$module" wireless-modules/
  done
done
exit "$failed"
