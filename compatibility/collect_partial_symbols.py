"""Collect CRCs emitted by selected objects; this is not a full Module.symvers."""
from pathlib import Path
import json
import re

objects = (
    'kernel/module/.version.o.cmd',
    'drivers/interconnect/.core.o.cmd',
    'net/wireless/.core.o.cmd',
    'net/wireless/.util.o.cmd',
)
symbols = {}
counts = {}
for relative in objects:
    source = Path('rom-kernel/out') / relative
    matches = re.findall(r'#SYMVER\s+(\w+)\s+(0x[0-9a-fA-F]+)', source.read_text())
    if not matches:
        raise SystemExit(f'No symbol CRC metadata in {relative}')
    counts[relative] = len(matches)
    for name, value in matches:
        crc = int(value, 16)
        if name in symbols and symbols[name] != crc:
            raise SystemExit(f'Conflicting generated CRCs for {name}')
        symbols[name] = crc
for required in ('module_layout', 'icc_set_bw', 'devm_of_icc_get', 'wiphy_register'):
    if required not in symbols:
        raise SystemExit(f'Required representative symbol missing: {required}')
root = Path('probe-evidence')
(root / 'partial-symbol-probe.tsv').write_text(''.join(
    f'0x{crc:08x}\t{name}\tvmlinux\tPROBE_ONLY\n'
    for name, crc in sorted(symbols.items())))
report = {'scope': 'Partial object CRC probe, not a complete kernel symbol table',
          'objects': counts, 'symbol_count': len(symbols),
          'limits': ['No full ABI pass can be inferred from this subset',
                     'LLVM 22 apt build is not the ROM Android r596125 compiler']}
(root / 'partial-probe-scope.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
