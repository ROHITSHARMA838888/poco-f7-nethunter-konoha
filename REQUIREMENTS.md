# Poco F7 / onyx NetHunter kernel

- Target ROM: Project_Infinity-X-4.1-onyx-23.10.2026-GAPPS-OFFICIAL.zip, verified locally. OTA SDK 37, security patch 2026-10-01. Android version must be checked against partition properties because OTA fingerprint contains Android 15.
- Upstream: https://github.com/onyx-oss/konoha-kernel-gki
- Verified main commit: d6b71af752d00499a238ceff5bab30592cc8d0a8; Linux 6.6.143.
- Build on GitHub Actions Ubuntu; local WSL is unnecessary.
- Required features: USB HID gadget, TP-Link Archer T2U Plus AC600, and TP-Link TL-WN722N external Wi-Fi support.
- Verify USB IDs and hardware revisions before selecting adapter drivers. Runtime monitor/injection functionality is not yet validated.
- Upstream konoha_defconfig enables USB_CONFIGFS_F_HID but disables CFG80211 and WLAN_VENDOR_REALTEK.
- Preserve kernel/vendor KMI compatibility and inspect ROM boot/vendor modules before claiming compatibility.
- This is an independent build repository. Preserve upstream license and provenance when retrieving source.
- No flashing authorized. A successful compilation alone does not establish boot or runtime functionality.

## Status
Repository initialized and requirements recorded. Kernel configuration, driver integration and CI workflow remain to be implemented. No build has run.
