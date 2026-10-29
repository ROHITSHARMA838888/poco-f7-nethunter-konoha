#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C
source drivers.lock
mkdir -p external probe-evidence verified-driver-files
failed=0
expected_release=$(cat rom-kernel/out/include/config/kernel.release)
for driver in rtl8812au rtl8188eus; do
  if [ "$driver" = rtl8812au ]; then
    remote="$RTL8812AU_REPOSITORY"; revision="$RTL8812AU_COMMIT"; usb_id=0120
  else
    remote="$RTL8188EUS_REPOSITORY"; revision="$RTL8188EUS_COMMIT"; usb_id=010C
  fi
  git init "external/$driver"
  git -C "external/$driver" remote add origin "$remote"
  git -C "external/$driver" fetch --depth=1 origin "$revision"
  git -C "external/$driver" checkout --detach FETCH_HEAD
  test "$(git -C "external/$driver" rev-parse HEAD)" = "$revision"
  python3 compatibility/prepare_rom_driver.py "external/$driver"
  git -C "external/$driver" diff --check
  git -C "external/$driver" diff > "probe-evidence/$driver-source-fixes.patch"
  if ! make -k -j"$(nproc)" -C rom-kernel O=out ARCH=arm64 LLVM=-22 \
      M="$GITHUB_WORKSPACE/external/$driver" \
      CONFIG_88XXAU=m CONFIG_RTL8188EU=m CONFIG_PLATFORM_I386_PC=n \
      USER_EXTRA_CFLAGS="-DCONFIG_LITTLE_ENDIAN -DCONFIG_IOCTL_CFG80211 -DRTW_USE_CFG80211_STA_EVENT" \
      modules 2>&1 | tee "probe-evidence/$driver-build.log"; then
    failed=1
    continue
  fi
  mapfile -t modules < <(find "external/$driver" -name '*.ko' -type f)
  if [ "${#modules[@]}" -ne 1 ]; then
    echo "Expected one driver module for $driver; found ${#modules[@]}"
    failed=1
    continue
  fi
  module="${modules[0]}"
  {
    llvm-readelf-22 -h "$module" | grep 'Machine:.*AArch64'
    vermagic=$(modinfo -F vermagic "$module")
    test "${vermagic%% *}" = "$expected_release"
    modinfo "$module"
    modinfo -F alias "$module" | grep -i "usb:v2357p${usb_id}"
    sha256sum "$module"
  } 2>&1 | tee "probe-evidence/$driver-verification.log"
  cp "$module" verified-driver-files/
  if [ -f "external/$driver/Module.symvers" ]; then
    cp "external/$driver/Module.symvers" "probe-evidence/$driver-Module.symvers"
  fi
done
exit "$failed"
