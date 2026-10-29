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
    # Snapshot and validate the hardware path count before serializing
    # presence words or indexing the four-entry per-path PHY array.
    assert function.count('pHalData->NumTotalRFPath') == 4
    function = function.replace('pHalData->NumTotalRFPath', 'rf_paths')
    declaration = '\tu32 tmp_32bit;\n\tint i;'
    assert function.count(declaration) == 1
    function = function.replace(declaration, declaration + '\n'
        '\tu8 rf_paths = pHalData->NumTotalRFPath;\n\n'
        '\tif (rf_paths > ARRAY_SIZE(pattrib->phy_info.rx_pwr))\n'
        '\t\treturn _FAIL;')
    # Serialize at most four words at fixed bounded offsets. Mutating
    # rt_len inside the variable-bound loop leaves Clang22's FORTIFY
    # object-size analysis with an overflowing loop path even after the
    # count guard. The new loop preserves every valid wire bitmap.
    first = function.index('\tif(rf_paths>0 && pattrib->physt) {')
    last = function.index('\n#ifdef CONFIG_RTL8814A', first)
    function = function[:first] + '''\tif (rf_paths > 0 && pattrib->physt) {
\t\trtap_hdr->it_present |= (1 << IEEE80211_RADIOTAP_EXT) |
\t\t\t(1 << IEEE80211_RADIOTAP_RADIOTAP_NAMESPACE);
\t\tfor (i = 0; i < ARRAY_SIZE(pattrib->phy_info.rx_pwr); i++) {
\t\t\tif (i >= rf_paths)
\t\t\t\tbreak;
\t\t\ttmp_32bit = (1 << IEEE80211_RADIOTAP_ANTENNA) |
\t\t\t\t(1 << IEEE80211_RADIOTAP_DBM_ANTSIGNAL);
\t\t\tif (i + 1 < rf_paths)
\t\t\t\ttmp_32bit |= (1 << IEEE80211_RADIOTAP_EXT) |
\t\t\t\t\t(1 << IEEE80211_RADIOTAP_RADIOTAP_NAMESPACE);
\t\t\tmemcpy(&hdr_buf[sizeof(*rtap_hdr) + i * sizeof(tmp_32bit)],
\t\t\t       &tmp_32bit, sizeof(tmp_32bit));
\t\t}
\t\trt_len += rf_paths * sizeof(tmp_32bit);
\t}
''' + function[last:]
    path.write_text(text[:start] + function + text[end:])
    print('Bound radiotap path count and serialized presence words at fixed offsets; FORTIFY remains enabled')
