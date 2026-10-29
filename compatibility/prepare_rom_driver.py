"""Apply reviewed base fixes and bound the radiotap antenna metadata."""
from pathlib import Path
import runpy
import sys

runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/prepare-driver.py'),
               run_name='__main__')
root = Path(sys.argv[1])
if root.name == 'rtl8812au':
    path = root / 'core/rtw_recv.c'
    text = path.read_text()
    start = text.index('sint fill_radiotap_hdr(')
    end = text.index('\n#if (LINUX_VERSION_CODE >= KERNEL_VERSION(2, 6, 24))', start)
    function = text[start:end]
    # The 64-byte radiotap buffer accommodates up to four RF paths.
    # An unchecked u8 path count permits the extended-present loop to
    # pass byte64; Clang22 flags this loop at original line4011.
    # Snapshot the count once so later aliasing cannot invalidate the bound.
    assert function.count('pHalData->NumTotalRFPath') == 4
    function = function.replace('pHalData->NumTotalRFPath', 'rf_paths')
    declaration = '\tu32 tmp_32bit;\n\tint i;'
    assert function.count(declaration) == 1
    function = function.replace(declaration, declaration + '\n'
        '\tu8 rf_paths = pHalData->NumTotalRFPath;\n\n'
        '\tif (rf_paths > ARRAY_SIZE(pattrib->phy_info.rx_pwr))\n'
        '\t\treturn _FAIL;')
    # Keep the fixed typed header distinct from the larger byte buffer.
    # Casting hdr_buf to the eight-byte radiotap struct lets object-size
    # analysis narrow subsequent writes through that aliased storage.
    # Compose the same eight header bytes only after all optional fields.
    old = '\tstruct ieee80211_radiotap_header *rtap_hdr = NULL;'
    assert function.count(old) == 1
    function = function.replace(old,
        '\tstruct ieee80211_radiotap_header rtap_fixed = {0};\n'
        '\tstruct ieee80211_radiotap_header *rtap_hdr = &rtap_fixed;')
    old = '\trtap_hdr = (struct ieee80211_radiotap_header *)&hdr_buf[0];\n'
    assert function.count(old) == 1
    function = function.replace(old, '')
    old = '\t\tmemcpy(ptr, rtap_hdr, rt_len);'
    assert function.count(old) == 1
    function = function.replace(old,
        '\t\tmemcpy(hdr_buf, rtap_hdr, sizeof(*rtap_hdr));\n'
        '\t\tmemcpy(ptr, hdr_buf, rt_len);')
    path.write_text(text[:start] + function + text[end:])
    print('Bound radiotap RF paths and separated fixed header storage; FORTIFY remains enabled')
