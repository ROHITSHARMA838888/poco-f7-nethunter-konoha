from pathlib import Path

p = Path('kernel/kernel/module/main.c')
s = p.read_text()
anchor = '#include <asm/cacheflush.h>'
assert s.count(anchor) == 1, 'Unexpected module source header layout'
s = s.replace(anchor, anchor + '\n#include <asm/patching.h>')
# module.name is an embedded array; checking its address is always true.
assert s.count('!mod || !mod->name') == 5, 'Unexpected module name guards'
s = s.replace('!mod || !mod->name', '!mod')
unused = '\tstatic bool kp_dfc = false, kp_ps = false;'
assert s.count(unused) == 1, 'Unexpected unused probe state'
s = s.replace(unused, '\tstatic bool kp_dfc __maybe_unused = false, kp_ps __maybe_unused = false;')
p.write_text(s)

# Keep LZ4 HC's local macros separate from Linux minmax.h definitions.
import re
p = Path('kernel/lib/lz4/lz4hc.c')
s = p.read_text()
assert '#define MIN(a,b)' in s and '#define MAX(a,b)' in s
s = re.sub(r'\bMIN\b', 'LZ4HC_MIN', s)
s = re.sub(r'\bMAX\b', 'LZ4HC_MAX', s)
p.write_text(s)
