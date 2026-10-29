"""Trace the original FORTIFY diagnostic; this creates no deployable driver."""
from pathlib import Path
import re
import shlex
import subprocess

root = Path.cwd()
metadata = root / 'external/rtl8812au/core/.rtw_recv.o.cmd'
commands = [line.split(' := ', 1)[1] for line in metadata.read_text().splitlines()
            if ' := ' in line and ' -c -o ' in line and 'rtw_recv.c' in line]
if len(commands) != 1:
    raise SystemExit('Expected one recorded rtw_recv.c compiler command')
argv = shlex.split(commands[0].split(';', 1)[0])
if not Path(argv[0]).name.startswith('clang'):
    raise SystemExit('Recorded command is not Clang')
argv[argv.index('-c'):argv.index('-c') + 1] = ['-S', '-emit-llvm']
ir = root / 'probe-evidence/rtw_recv.ll'
argv[argv.index('-o') + 1] = str(ir)
subprocess.run(argv, cwd=root / 'rom-kernel/out', check=True)
lines = ir.read_text().splitlines()
nodes = {line.split(' = ', 1)[0]: line for line in lines if re.match(r'!\d+ = ', line)}
output = ['DIAGNOSTIC ONLY: original file, attribute-warning temporarily nonfatal to inspect IR.']
function = ''
for index, line in enumerate(lines):
    if line.startswith('define '):
        function = line[:240]
    if 'call ' not in line or '@__write_overflow_field(' not in line:
        continue
    output += [function, *lines[max(0, index-3):index+3]]
    pending = re.findall(r'!dbg (!\d+)', line)
    seen = set()
    while pending and len(seen) < 30:
        key = pending.pop()
        if key in seen or key not in nodes:
            continue
        seen.add(key)
        node = nodes[key]
        output.append(node)
        pending.extend(re.findall(r'(?:scope|inlinedAt|file): (!\d+)', node))
report = '\n'.join(output) + '\n'
(root / 'probe-evidence/fortify-call-sites.log').write_text(report)
print(report)
metadata_copy = root / 'probe-evidence/rtw_recv.o.cmd.txt'
metadata_copy.write_text(metadata.read_text())
