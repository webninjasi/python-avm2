from itertools import count
from struct import Struct
from typing import Union

D64 = Struct('<d')
U16 = Struct('<H')
U32 = Struct('<I')


class MemoryViewReader:
    """
    Reads a memory view as a structured stream.
    """

    def __init__(self, buffer: Union[memoryview, bytes]):
        self.buffer = buffer if isinstance(buffer, memoryview) else memoryview(buffer)
        self.position = 0

    def __repr__(self) -> str:
        return f'MemoryViewReader(buffer={self.buffer!r}, position={self.position!r})'

    def is_eof(self) -> bool:
        return self.position >= len(self.buffer)

    def read(self, size: int) -> memoryview:
        """
        Read the number of bytes.
        """
        value = self.buffer[self.position:self.position + size]
        self.position += len(value)
        return value

    def read_all(self) -> memoryview:
        """
        Read everything until the end.
        """
        value = self.buffer[self.position:]
        self.position += len(value)
        return value

    def skip(self, size: int) -> int:
        """
        Skip the number of bytes.
        """
        self.position += size
        return self.position

    def read_u8(self) -> int:
        """
        Read one-byte unsigned integer value.
        """
        value: int = self.buffer[self.position]
        self.position += 1
        return value

    def read_u16(self) -> int:
        """
        Read two-byte unsigned integer value.
        """
        # noinspection PyTypeChecker
        value, = U16.unpack(self.buffer[self.position:self.position + 2])
        self.position += 2
        return value

    def read_u32(self) -> int:
        """
        Read four-byte unsigned integer value.
        """
        # noinspection PyTypeChecker
        value, = U32.unpack(self.buffer[self.position:self.position + 4])
        self.position += 4
        return value

    def skip_rect(self):
        """
        Skip RECT record.
        """
        n_bits = self.read_u8()
        self.skip(((n_bits >> 3) * 4 - 3 + 8) // 8)  # `n_bits` times 4 minus 3 bits (already read)

    def read_until(self, sentinel: int) -> memoryview:
        """
        Read everything until the specified value.
        """
        for length in count():
            if self.buffer[self.position + length] == sentinel:
                value = self.buffer[self.position:self.position + length]
                self.position += length + 1
                return value

    def read_string(self) -> str:
        """
        Read null-terminated string.
        """
        return bytes(self.read_until(0)).decode('utf-8')

    def read_int(self, unsigned=True) -> int:
        """
        Read variable-length encoded 32-bit unsigned or signed integer value: ASVM2 u30, u32 and s32.
        """

        value = 0
        for i in range(0, 35, 7):
            byte = self.read_u8()
            value |= (byte & 0x7F) << i
            if not byte & 0x80:
                break

        if unsigned:
            return value

        return self.extend_sign(value, 0x00000040 << i)

    @staticmethod
    def extend_sign(value: int, mask: int) -> int:
        """
        Performs sign extension.
        https://stackoverflow.com/a/32031543/359730
        """
        # mask = 1 << (n_bit - 1)
        return (value & (mask - 1)) - (value & mask)

    def read_d64(self) -> float:
        # noinspection PyTypeChecker
        value, = D64.unpack(self.read(8))  # type: float
        return value

    def read_s24(self) -> int:
        value, = U32.unpack(self.read(3).tobytes() + b'\x00')
        return self.extend_sign(value, 0x00800000)
