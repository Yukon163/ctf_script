class IO_FILE_plus_struct:
    def __init__(self):
        # 初始化所有字段
        self._flags = 0
        self._IO_read_ptr = 0
        self._IO_read_end = 0
        self._IO_read_base = 0
        self._IO_write_base = 0
        self._IO_write_ptr = 0
        self._IO_write_end = 0
        self._IO_buf_base = 0
        self._IO_buf_end = 0
        self._IO_save_base = 0
        self._IO_backup_base = 0
        self._IO_save_end = 0
        self._markers = 0
        self._chain = 0
        self._fileno = 0
        self._flags2 = 0
        self._old_offset = 0
        self._cur_column = 0
        self._vtable_offset = 0
        self._shortbuf = 0
        self._lock = 0
        self._offset = 0
        self._codecvt = 0
        self._wide_data = 0
        self._freeres_list = 0
        self._freeres_buf = 0
        self.__pad5 = 0
        self._mode = 0
        self._unused2 = 0
        self.vtable = 0

    def pack(self):
        # 根据实际偏移量将字段打包为字节串
        return flat(
            self._flags,  # 0x0
            self._IO_read_ptr,  # 0x8
            self._IO_read_end,  # 0x10
            self._IO_read_base,  # 0x18
            self._IO_write_base,  # 0x20
            self._IO_write_ptr,  # 0x28
            self._IO_write_end,  # 0x30
            self._IO_buf_base,  # 0x38
            self._IO_buf_end,  # 0x40
            self._IO_save_base,  # 0x48
            self._IO_backup_base,  # 0x50
            self._IO_save_end,  # 0x58
            self._markers,  # 0x60
            self._chain,  # 0x68
            self._fileno,  # 0x70
            p32(self._flags2),  # 0x74 (4-byte integer)
            self._old_offset,  # 0x78
            p16(self._cur_column),  # 0x80 (2-byte integer)
            p8(self._vtable_offset),  # 0x82 (1-byte integer)
            p8(self._shortbuf),  # 0x83 (1-byte integer)
            self._lock,  # 0x88
            self._offset,  # 0x90
            self._codecvt,  # 0x98
            self._wide_data,  # 0xa0
            self._freeres_list,  # 0xa8
            self._freeres_buf,  # 0xb0
            self.__pad5,  # 0xb8
            self._mode,  # 0xc0
            self._unused2,  # 0xc4 (4-byte integer)
            b'\x00' * (0xd8 - 0xc8),  # 填充至 vtable 偏移位置
            self.vtable  # 0xd8
        )