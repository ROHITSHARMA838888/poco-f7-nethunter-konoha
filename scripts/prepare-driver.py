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

def replace_once(path, old, new):
    text = path.read_text()
    assert text.count(old) == 1, f'Unexpected source layout: {path}: {old!r}'
    path.write_text(text.replace(old, new))

if root.name == 'rtl8812au':
    # These NDIS helpers have no Linux callers. Their uninitialized pointers
    # are initialized only in PLATFORM_WINDOWS code, so scope the helpers too.
    header = root / 'include/rtw_recv.h'
    replace_once(header,
                 '__inline static _buffer *get_rxbuf_desc(',
                 '#ifdef PLATFORM_WINDOWS\n__inline static _buffer *get_rxbuf_desc(')
    replace_once(header,
                 '__inline static union recv_frame *rxmem_to_recvframe(',
                 '#endif /* PLATFORM_WINDOWS */\n\n__inline static union recv_frame *rxmem_to_recvframe(')
    replace_once(header,
                 '__inline static union recv_frame *pkt_to_recvframe(',
                 '#ifdef PLATFORM_WINDOWS\n__inline static union recv_frame *pkt_to_recvframe(')
    replace_once(header,
                 '__inline static sint get_recvframe_len(',
                 '#endif /* PLATFORM_WINDOWS */\n\n__inline static sint get_recvframe_len(')

    # Reject copy failures before using key_type, and copy only supplied bytes.
    debug = root / 'core/rtw_debug.c'
    text = debug.read_text()
    start = text.index('ssize_t proc_set_tx_deauth(')
    end = text.index('\nssize_t ', start + 1)
    function = text[start:end]
    assert function.count('char tmp[16];') == 1
    function = function.replace('char tmp[16];', 'char tmp[16] = {0};')
    old = 'if (buffer && !copy_from_user(tmp, buffer, sizeof(tmp))) {'
    assert function.count(old) == 1
    function = function.replace(old,
        'if (!buffer || copy_from_user(tmp, buffer, count))\n'
        '\t\treturn -EFAULT;\n\n\t{')
    debug.write_text(text[:start] + function + text[end:])
elif root.name == 'rtl8188eus':
    replace_once(root / 'hal/rtl8188e/usb/usb_halinit.c',
                 'if ((IS_FULL_SPEED_USB(Adapter))',
                 'if (IS_FULL_SPEED_USB(Adapter)')
