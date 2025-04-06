from __future__ import annotations

from dataclasses import dataclass

from avm2.swf.enums import DoABCTagFlags, TagType
from avm2.io import MemoryViewReader


@dataclass
class Tag:
    type_: TagType
    raw: memoryview


@dataclass
class DoABCTag:
    flags: DoABCTagFlags
    name: str
    abc_file: memoryview

    def __init__(self, raw: memoryview):
        reader = MemoryViewReader(raw)
        self.flags = DoABCTagFlags(reader.read_u32())
        self.name = reader.read_string()
        self.abc_file = reader.read_all()


@dataclass
class SymbolsTag:
    tags: dict[int, str]

    def __init__(self, raw: memoryview):
        reader = MemoryViewReader(raw)
        count = reader.read_u16()
        self.tags = {
            reader.read_u16(): reader.read_string()
            for _ in range(count)
        }


@dataclass
class DefineBinaryDataTag:
    tag: int
    reserved: int
    data: str

    def __init__(self, raw: memoryview):
        reader = MemoryViewReader(raw)
        self.tag = reader.read_u16()
        self.reserved = reader.read_u32()
        self.data = reader.read_all()
