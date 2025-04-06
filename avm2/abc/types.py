from __future__ import annotations

import math
from dataclasses import dataclass
from functools import partial
from typing import Optional, List, Union, NewType

from avm2.abc.enums import (
    ClassFlags,
    ConstantKind,
    MethodFlags,
    MultinameKind,
    NamespaceKind,
    TraitAttributes,
    TraitKind,
)
from avm2.abc.parser import read_array, read_array_with_default, read_string
from avm2.io import MemoryViewReader

ABCStringIndex = NewType('ABCStringIndex', int)
ABCNamespaceIndex = NewType('ABCNamespaceIndex', int)
ABCNamespaceSetIndex = NewType('ABCNamespaceSetIndex', int)
ABCMultinameIndex = NewType('ABCMultinameIndex', int)
ABCMethodIndex = NewType('ABCMethodIndex', int)
ABCMethodBodyIndex = NewType('ABCMethodBodyIndex', int)
ABCMetadataIndex = NewType('ABCMetadataIndex', int)
ABCClassIndex = NewType('ABCClassIndex', int)
ABCScriptIndex = NewType('ABCScriptIndex', int)


@dataclass
class ABCFile:
    minor_version: int
    major_version: int
    constant_pool: ASConstantPool
    methods: List[ASMethod]
    metadata: List[ASMetadata]
    instances: List[ASInstance]
    classes: List[ASClass]
    scripts: List[ASScript]
    method_bodies: List[ASMethodBody]

    def __init__(self, reader: MemoryViewReader):
        self.minor_version = reader.read_u16()
        self.major_version = reader.read_u16()
        self.constant_pool = ASConstantPool(reader)
        self.methods = read_array(reader, ASMethod)
        self.metadata = read_array(reader, ASMetadata)
        class_count = reader.read_int()
        self.instances = read_array(reader, ASInstance, class_count)
        self.classes = read_array(reader, ASClass, class_count)
        self.scripts = read_array(reader, ASScript)
        self.method_bodies = read_array(reader, ASMethodBody)


@dataclass
class ASConstantPool:
    integers: List[int]
    unsigned_integers: List[int]
    doubles: List[float]
    strings: List[str]
    namespaces: List[ASNamespace]
    ns_sets: List[ASNamespaceSet]
    multinames: List[ASMultiname]

    def __init__(self, reader: MemoryViewReader):
        self.integers = read_array_with_default(reader, partial(MemoryViewReader.read_int, unsigned=False), 0)
        self.unsigned_integers = read_array_with_default(reader, MemoryViewReader.read_int, 0)
        self.doubles = read_array_with_default(reader, MemoryViewReader.read_d64, math.nan)
        self.strings = read_array_with_default(reader, read_string, None)
        self.namespaces = read_array_with_default(reader, ASNamespace, None)
        self.ns_sets = read_array_with_default(reader, ASNamespaceSet, None)
        self.multinames = read_array_with_default(reader, ASMultiname, None)


@dataclass
class ASNamespace:
    kind: NamespaceKind
    name_index: ABCStringIndex

    def __init__(self, reader: MemoryViewReader):
        self.kind = NamespaceKind(reader.read_u8())
        self.name_index = reader.read_int()


@dataclass
class ASNamespaceSet:
    namespaces: List[ABCNamespaceIndex]

    def __init__(self, reader: MemoryViewReader):
        self.namespaces = read_array(reader, MemoryViewReader.read_int)


@dataclass
class ASMultiname:
    kind: MultinameKind
    namespace_index: Optional[ABCNamespaceIndex] = None
    name_index: Optional[ABCStringIndex] = None
    namespace_set_index: Optional[ABCNamespaceSetIndex] = None
    q_name_index: Optional[ABCMultinameIndex] = None
    type_indices: Optional[List[ABCMultinameIndex]] = None

    def __init__(self, reader: MemoryViewReader):
        self.kind = MultinameKind(reader.read_u8())
        if self.kind in (MultinameKind.Q_NAME, MultinameKind.Q_NAME_A):
            self.namespace_index = reader.read_int()
            self.name_index = reader.read_int()
        elif self.kind in (MultinameKind.RTQ_NAME, MultinameKind.RTQ_NAME_A):
            self.name_index = reader.read_int()
        elif self.kind in (MultinameKind.RTQ_NAME_L, MultinameKind.RTQ_NAME_LA):
            pass
        elif self.kind in (MultinameKind.MULTINAME, MultinameKind.MULTINAME_A):
            self.name_index = reader.read_int()
            self.namespace_set_index = reader.read_int()
        elif self.kind in (MultinameKind.MULTINAME_L, MultinameKind.MULTINAME_LA):
            self.namespace_set_index = reader.read_int()
        elif self.kind == MultinameKind.TYPE_NAME:
            self.q_name_index = reader.read_int()
            self.type_indices = read_array(reader, MemoryViewReader.read_int)
        else:
            assert False, 'unreachable code'

    def qualified_name(self, constant_pool: ASConstantPool) -> str:
        assert self.kind == MultinameKind.Q_NAME, self.kind
        assert self.namespace_index
        assert self.name_index
        namespace = constant_pool.namespaces[self.namespace_index]
        #assert namespace.name_index
        return f'{constant_pool.strings[namespace.name_index]}.{constant_pool.strings[self.name_index]}'.strip('.')


@dataclass
class ASMethod:
    param_count: int
    return_type_index: ABCMultinameIndex
    param_type_indices: List[ABCMultinameIndex]
    name_index: ABCStringIndex
    flags: MethodFlags
    options: Optional[List[ASOptionDetail]] = None
    param_name_indices: Optional[List[ABCStringIndex]] = None

    def __init__(self, reader: MemoryViewReader):
        self.param_count = reader.read_int()
        self.return_type_index = reader.read_int()
        self.param_type_indices = read_array(reader, MemoryViewReader.read_int, self.param_count)
        self.name_index = reader.read_int()
        self.flags = MethodFlags(reader.read_u8())
        if MethodFlags.HAS_OPTIONAL in self.flags:
            self.options = read_array(reader, ASOptionDetail)
        if MethodFlags.HAS_PARAM_NAMES in self.flags:
            self.param_name_indices = read_array(reader, MemoryViewReader.read_int, self.param_count)


@dataclass
class ASOptionDetail:
    value: int
    kind: ConstantKind

    def __init__(self, reader: MemoryViewReader):
        self.value = reader.read_int()
        self.kind = ConstantKind(reader.read_u8())


@dataclass
class ASMetadata:
    name_index: ABCStringIndex
    items: List[ASItem]

    def __init__(self, reader: MemoryViewReader):
        self.name_index = reader.read_int()
        self.items = read_array(reader, ASItem)


@dataclass
class ASItem:
    key_index: ABCStringIndex
    value_index: ABCStringIndex

    def __init__(self, reader: MemoryViewReader):
        self.key_index = reader.read_int()
        self.value_index = reader.read_int()


@dataclass
class ASInstance:
    name_index: ABCMultinameIndex
    super_name_index: ABCMultinameIndex
    flags: ClassFlags
    interface_indices: List[ABCMultinameIndex]
    init_index: ABCMethodIndex
    traits: List[ASTrait]
    protected_namespace_index: Optional[ABCNamespaceIndex] = None

    def __init__(self, reader: MemoryViewReader):
        self.name_index = reader.read_int()
        self.super_name_index = reader.read_int()
        self.flags = ClassFlags(reader.read_u8())
        if ClassFlags.PROTECTED_NS in self.flags:
            self.protected_namespace_index = reader.read_int()
        self.interface_indices = read_array(reader, MemoryViewReader.read_int)
        self.init_index = reader.read_int()
        self.traits = read_array(reader, ASTrait)


@dataclass
class ASTrait:
    name_index: ABCMultinameIndex
    kind: TraitKind
    attributes: TraitAttributes
    data: Union[ASTraitSlot, ASTraitClass, ASTraitFunction, ASTraitMethod]
    metadata: Optional[List[ABCMetadataIndex]] = None

    def __init__(self, reader: MemoryViewReader):
        self.name_index = reader.read_int()
        kind = reader.read_u8()
        self.kind = TraitKind(kind & 0x0F)
        self.attributes = TraitAttributes(kind >> 4)
        if self.kind in (TraitKind.SLOT, TraitKind.CONST):
            self.data = ASTraitSlot(reader)
        elif self.kind == TraitKind.CLASS:
            self.data = ASTraitClass(reader)
        elif self.kind == TraitKind.FUNCTION:
            self.data = ASTraitFunction(reader)
        elif self.kind in (TraitKind.METHOD, TraitKind.GETTER, TraitKind.SETTER):
            self.data = ASTraitMethod(reader)
        else:
            assert False, 'unreachable code'
        if TraitAttributes.METADATA in self.attributes:
            self.metadata = read_array(reader, MemoryViewReader.read_int)


@dataclass
class ASTraitSlot:
    slot_id: int
    type_name_index: ABCMultinameIndex
    vindex: int
    vkind: Optional[ConstantKind] = None

    def __init__(self, reader: MemoryViewReader):
        self.slot_id = reader.read_int()
        self.type_name_index = reader.read_int()
        self.vindex = reader.read_int()
        if self.vindex:
            self.vkind = ConstantKind(reader.read_u8())


@dataclass
class ASTraitClass:
    slot_id: int
    class_index: ABCClassIndex

    def __init__(self, reader: MemoryViewReader):
        self.slot_id = reader.read_int()
        self.class_index = reader.read_int()


@dataclass
class ASTraitFunction:
    slot_id: int
    function_index: ABCMethodIndex

    def __init__(self, reader: MemoryViewReader):
        self.slot_id = reader.read_int()
        self.function_index = reader.read_int()


@dataclass
class ASTraitMethod:
    disposition_id: int
    method_index: ABCMethodIndex

    def __init__(self, reader: MemoryViewReader):
        self.disposition_id = reader.read_int()
        self.method_index = reader.read_int()


@dataclass
class ASClass:
    init_index: ABCMethodIndex
    traits: List[ASTrait]

    def __init__(self, reader: MemoryViewReader):
        self.init_index = reader.read_int()
        self.traits = read_array(reader, ASTrait)


@dataclass
class ASScript:
    init_index: ABCMethodIndex
    traits: List[ASTrait]

    def __init__(self, reader: MemoryViewReader):
        self.init_index = reader.read_int()
        self.traits = read_array(reader, ASTrait)


@dataclass
class ASMethodBody:
    method_index: ABCMethodIndex
    max_stack: int
    local_count: int
    init_scope_depth: int
    max_scope_depth: int
    code: memoryview
    exceptions: List[ASException]
    traits: List[ASTrait]

    def __init__(self, reader: MemoryViewReader):
        self.method_index = reader.read_int()
        self.max_stack = reader.read_int()
        self.local_count = reader.read_int()
        self.init_scope_depth = reader.read_int()
        self.max_scope_depth = reader.read_int()
        self.code = reader.read(reader.read_int())
        self.exceptions = read_array(reader, ASException)
        self.traits = read_array(reader, ASTrait)


@dataclass
class ASException:
    from_: int
    to: int
    target: int
    exc_type_index: ABCStringIndex
    var_name_index: ABCStringIndex

    def __init__(self, reader: MemoryViewReader):
        self.from_ = reader.read_int()
        self.to = reader.read_int()
        self.target = reader.read_int()
        self.exc_type_index = reader.read_int()
        self.var_name_index = reader.read_int()
