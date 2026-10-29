"""Report the ROM baseline ABI probe without changing any CRC values."""
from pathlib import Path
import json,re
root=Path('probe-evidence')
root.mkdir(exist_ok=True)
cmd=Path('rom-kernel/out/kernel/module/.version.o.cmd').read_text()
match=re.search(r'#SYMVER\s+module_layout\s+(0x[0-9a-fA-F]+)',cmd)
if not match:
    raise SystemExit('module_layout CRC not emitted in version.o command metadata')
actual=int(match.group(1),16)
expected=0x4e276f37
report={'source_commit':'7750565ada3d57e195798519b005d2b038e888c1',
        'expected_module_layout':hex(expected),'actual_module_layout':hex(actual),
        'match':actual==expected,
        'toolchain_scope':'System Clang 18 diagnostic probe, not a reproduction of ROM Android Clang 22',
        'limits':['One symbol only; matching it is necessary but not sufficient for ROM compatibility',
                  'No kernel Image, root changes, installer or runtime test produced by this probe']}
(root/'abi-probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if actual!=expected:
    raise SystemExit('Baseline CRC mismatch: stop before producing a candidate kernel')
