# ROM baseline ABI checkpoint

The exact Infinity-X / onyx kernel source and config now produce a symbol table with no CRC mismatches against the supplied ROM modules.

- Source: xiaomi-onyx-playground/android_kernel_xiaomi_sm8735 at `7750565ada3d57e195798519b005d2b038e888c1` (Linux 6.6.142).
- Build: [40845707042](https://github.com/ROHITSHARMA838888/poco-f7-nethunter-konoha/actions/runs/40845707042), commit `507d880d770d99534be9c9ff351e6fc84dd0a096`.
- Compiler: official apt LLVM 22.1.8; this is not the ROM's exact Android Clang r596125.
- BTF settings and `CONFIG_CC_HAS_COUNTED_BY` are retained; `module_layout` matches `0x4e276f37`.
- Local comparison: 959 module files / 575 unique modules, 48,681 import-version records; zero CRC mismatches. All 534 import names absent from the baseline symbol table have original ROM-module providers with matching export CRCs.
- All 96 symbol names that mismatched in the earlier Clang18 baseline now match.
- Evidence artifact SHA256: `0aa43b2de0ee29778db3b9b3e56a242fa91f20f3a7a7a21d4febff56fe2f995f`.

This is static import/export CRC verification of the ROM-source baseline. It does not establish phone boot, CFI/runtime behavior, KernelSU root, USB HID gadget operation or adapter functionality. The earlier Linux 6.6.143 Konoha candidate remains incompatible in the recorded CRC comparison.

The next candidate preparation adds pinned KernelSU Next, ath9k_htc and the two pinned external Realtek drivers, while preserving CFG80211/MAC80211 as modules and the existing configfs HID setting. That candidate must be built and compared again. No new root/adapter candidate on this baseline has been compiled yet, and no flash-ready installer is available.
