# ROM root/adapter build checkpoint

## Complete candidate verified — run40863319425

[Complete build and artifacts](https://github.com/ROHITSHARMA838888/poco-f7-nethunter-konoha/actions/runs/40863319425) succeeded at `d49868d71b68c7269ffe6785ccfb9d2d7a49a443`. Downloaded artifact ZIP digests, ZIP CRCs and per-file checksums passed. Actual Image is37,067,264 bytes, SHA256 `2f26ba841a9b3094943a06c60047a999cafd75a2a484670fbeb0cf0ab19c00f6`; embedded config confirms KernelSU, configfs HID and the required ROM ABI settings. All six compiled modules are AArch64, match the Image release, contain module BTF, and pass all630 import-version CRC and namespace checks.

The complete candidate's symbol table was compared locally against all959 ROM module files /575 unique modules: ZERO mismatches. All534 remaining import names have original ROM-module providers with matching CRCs. Evidence is saved locally under `build-evidence/rom-root-40863319425` and in the public artifacts. Combined binary artifact12894139374 digest: `eb19116a38bffed8f3f554b1f5f091c761c83e55e4530e9985b131543f21d333`.

This completes compilation, artifact publication and static verification. These are test files, not a flashable installer. Phone boot/root grants, HID gadget operation and adapter operation remain untested; WN722N hardware revision/firmware still require confirmation.

The exact onyx ROM source/config, with pinned KernelSU Next and Atheros support added, has passed the full static ROM-module CRC comparison.

- Kernel source: xiaomi-onyx-playground/android_kernel_xiaomi_sm8735, commit `7750565ada3d57e195798519b005d2b038e888c1`, Linux6.6.142.
- KernelSU Next: `b427a3f9c2421a443f961007bfce66b25486643f`.
- Compiler: official apt LLVM22.1.8, not the exact Android Clang r596125 used for the supplied ROM.
- Root/ATH kernel compilation: [40852476542](https://github.com/ROHITSHARMA838888/poco-f7-nethunter-konoha/actions/runs/40852476542). Image/modules, KernelSU init symbol and preinit runner checks succeeded. That overall run failed later in rtl8812au.
- Local comparison of that root/ATH symbol table:959 module files /575 unique modules /48681 import-version records; zero CRC mismatches. All534 import names absent from its table have original ROM-module providers with matching export CRCs. module_layout matches `0x4e276f37`.

The rtl8812au failure was isolated to its radiotap extended-presence bitmap loop. The fix validates and snapshots the four-entry RF-path count and serializes at statically bounded offsets, preserving the valid wire bitmap sequence. Normal FORTIFY and Werror remain enabled.

Strict header-only validation [40862056606](https://github.com/ROHITSHARMA838888/poco-f7-nethunter-konoha/actions/runs/40862056606) passed at `af99ebf5165a95184543057e3a69c277bb5a4967`. Both actual `88XXau.ko` and `8188eu.ko` were linked; AArch64, matching release `6.6.142-4k-g7750565ada3d-dirty`, and USB aliases2357:0120 /2357:010c passed. This small test did not build vmlinux, so module BTF was not generated there. The subsequent complete build produces the full candidate outputs.

The complete workflow now uploads Image and Atheros dependencies before compiling external Realtek drivers. Individually verified Realtek modules are retained independently even if another driver fails. The combined test package is produced only when all stages succeed. This corrects the old ordering that lost a successful kernel Image when an external driver failed.

These are compiled test files, not a flashable installer. Phone boot, root grants, CFI/runtime behavior, HID gadget setup, adapter operation and WN722N hardware revision remain unverified. ath9k_htc needs separate firmware. The old6.6.143 Konoha candidate remains incompatible with the recorded ROM CRCs and must not be confused with these ROM-source builds.
