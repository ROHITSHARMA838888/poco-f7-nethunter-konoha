from pathlib import Path
import sys

root = Path(sys.argv[1])
p = root / 'Makefile'
s = p.read_text()
# GCC-only warning flag is rejected by Clang. Remove only that option.
if root.name == 'rtl8812au':
    flag = 'EXTRA_CFLAGS += -Wno-stringop-overread'
    assert s.count(flag) == 1, 'Unexpected rtl8812au flags'
    s = s.replace(flag, '# GCC-only stringop-overread option removed for Clang')
# Vendor packet IE structures use legacy trailing [0]/[1] arrays.
# Preserve those semantics rather than disabling array-bounds diagnostics.
s += '\nEXTRA_CFLAGS += -fstrict-flex-arrays=0\n'
# Keep legacy switch fallthrough warnings visible, without promoting them.
s += 'EXTRA_CFLAGS += -Wno-error=implicit-fallthrough\n'
p.write_text(s)
