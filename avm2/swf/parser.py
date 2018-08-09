from __future__ import annotations

import lzma
import zlib
from io import BytesIO, SEEK_CUR
from struct import Struct
from typing import BinaryIO, Iterable

from avm2.helpers import read_string, read_struct, read_value
from avm2.swf.types import DoABCTag, DoABCTagFlags, Signature, Tag, TagType

U16_STRUCT = Struct('<H')
U32_STRUCT = Struct('<I')

HEADER_STRUCT = Struct('<BHBI')
CODE_LENGTH_STRUCT = Struct('<H')
TAG_LENGTH_STRUCT = Struct('<I')


def parse(io: BinaryIO) -> Iterable[Tag]:
    """
    Parse SWF file and get an iterable of its tags.
    """
    signature, ws, version, file_length = read_struct(io, HEADER_STRUCT)  # type: int, int, int, int
    assert ws == 0x5357
    io = decompress(io, Signature(signature))
    skip_rect(io)
    io.seek(4, SEEK_CUR)  # frame rate and frame count
    return read_tags(io)


def decompress(io: BinaryIO, signature: Signature) -> BinaryIO:
    """
    Decompress the rest of an SWF file, depending on its signature.
    """
    if signature == Signature.UNCOMPRESSED:
        return io
    if signature == Signature.LZMA:
        # https://stackoverflow.com/a/39777419/359730
        io.seek(4, SEEK_CUR)  # skip compressed length
        return BytesIO(lzma.decompress(io.read(5) + b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF' + io.read()))
    if signature == Signature.ZLIB:
        return BytesIO(zlib.decompress(io.read()))
    assert False, 'unreachable code'


def skip_rect(io: BinaryIO):
    """
    Skip RECT record.
    """
    n_bits, = io.read(1)
    io.seek(((n_bits >> 3) * 4 - 3 + 8) // 8, SEEK_CUR)  # `n_bits` times 4 minus 3 bits (already read)


def read_tags(io: BinaryIO) -> Iterable[Tag]:
    """
    Read tags from the stream and get an iterable of tags.
    """
    while True:
        code_length: int = read_value(io, CODE_LENGTH_STRUCT)
        length = code_length & 0b111111
        if length == 0x3F:
            # Long tag header.
            length: int = read_value(io, TAG_LENGTH_STRUCT)
        try:
            type_ = TagType(code_length >> 6)
        except ValueError:
            # Unknown tag type. Skip the tag.
            io.seek(length, SEEK_CUR)
        else:
            yield Tag(type_=type_, raw=io.read(length))
            if type_ == TagType.END:
                break


def parse_do_abc_tag(tag: Tag) -> DoABCTag:
    """
    Parse DO_ABC tag.
    """
    assert tag.type_ == TagType.DO_ABC
    io = BytesIO(tag.raw)
    return DoABCTag(
        flags=DoABCTagFlags(read_value(io, U32_STRUCT)),
        name=read_string(io),
        abc_file=io.read(),
    )
