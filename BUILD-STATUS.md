# Verified build status

Build: [40830351000](https://github.com/ROHITSHARMA838888/poco-f7-nethunter-konoha/actions/runs/40830351000)

Build commit: `9ecd12918ad1bea7baab5a015a3e3bad762c2fa3`.

## Verified outputs
- ARM64 kernel Image: 33,933,824 bytes. KernelSU Next and USB HID enabled in resolved configuration.
- `88XXau.ko`: 76,327,096 bytes; USB alias includes `2357:0120` (Archer T2U Plus).
- `8188eu.ko`: 67,769,200 bytes; USB alias includes `2357:010c` (WN722N Realtek family).
- Both modules passed ELF AArch64 and matching kernel-release checks. Both vermagic strings: `6.6.143-Kono-Ha-Kernel SMP preempt mod_unload modversions aarch64`.
- Kernel output restored from the matching successful cache; all driver source patches and modinfo evidence are included in the external Wi-Fi artifact. Modules contain debugging information, hence their large uncompressed size.

## Sources
- Konoha: `onyx-oss/konoha-kernel-gki`, commit `d6b71af752d00499a238ceff5bab30592cc8d0a8`.
- KernelSU Next: `KernelSU-Next/KernelSU-Next`, commit `b427a3f9c2421a443f961007bfce66b25486643f`.
- Realtek driver revisions: see [drivers.lock](drivers.lock). Applied changes: [scripts/prepare-driver.py](scripts/prepare-driver.py) and artifact patches.

## Outstanding runtime and packaging work
Compilation success does not verify phone boot, root, HID use, Wi-Fi operation or ROM/vendor-module compatibility. This is not a flash-ready installer.

The kernel's built-in RTL8XXXU driver also matches `2357:010c`; validate the binding strategy before expecting the external 8188eu module to own WN722N automatically. WN722N hardware revision remains unknown; the Atheros v1 variant uses ATH9K_HTC and requires its firmware. Inspect the provided Infinity-X ROM boot/vendor metadata and module compatibility before packaging for device testing. No flashing has been performed.
