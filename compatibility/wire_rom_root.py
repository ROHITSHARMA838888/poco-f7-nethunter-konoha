"""Wire pinned KernelSU Next into the exact ROM source without ABI bypasses."""
from pathlib import Path

root = Path('rom-kernel')
assert (root / '.root_modules/KernelSU-Next/kernel/Kbuild').is_file()
makefile = root / 'drivers/Makefile'
kconfig = root / 'drivers/Kconfig'
m = makefile.read_text()
k = kconfig.read_text()
assert 'kernelsu' not in m and 'drivers/kernelsu/Kconfig' not in k
assert k.count('\nendmenu') == 1
makefile.write_text(m.rstrip() + '\n\nobj-$(CONFIG_KSU) += kernelsu/\n')
kconfig.write_text(k.replace('\nendmenu', '\nsource "drivers/kernelsu/Kconfig"\nendmenu'))
print('Added pinned KernelSU Next Kconfig and Kbuild wiring; no ABI checker changes')
