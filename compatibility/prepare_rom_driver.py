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
    # pass byte64; Clang22 reports the exact write at original line4011.
    # Snapshot the count once so later aliasing cannot invalidate the bound.
    assert function.count('pHalData->NumTotalRFPath') == 4
    function = function.replace('pHalData->NumTotalRFPath', 'rf_paths')
    declaration = '\tu32 tmp_32bit;\n\tint i;'
    assert function.count(declaration) == 1
    function = function.replace(declaration, declaration + '\n'
        '\tu8 rf_paths = pHalData->NumTotalRFPath;\n\n'
        '\tif (rf_paths > ARRAY_SIZE(pattrib->phy_info.rx_pwr))\n'
        '\t\treturn _FAIL;')
    path.write_text(text[:start] + function + text[end:])
    print('Bound radiotap RF paths to the PHY metadata array; FORTIFY remains enabled')
