from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Callable, ClassVar, Dict, Tuple, Type, TypeVar, NewType, Optional

import avm2.vm
from avm2.exceptions import ASReturnException, ASJumpException
from avm2.runtime import undefined, ASObject, ASString
from avm2.abc.parser import read_array
from avm2.io import MemoryViewReader
from avm2.abc.enums import ConstantKind, TraitKind


def read_instruction(reader: MemoryViewReader) -> Instruction:
    # noinspection PyCallingNonCallable
    return opcode_to_instruction[reader.read_u8()](reader)


u8 = NewType('u8', int)
u30 = NewType('u30', int)
uint = NewType('uint', int)
s24 = NewType('s24', int)


@dataclass
class Instruction:
    readers: ClassVar[Dict[str, Callable[[MemoryViewReader], Any]]] = {
        u8.__name__: MemoryViewReader.read_u8,
        u30.__name__: MemoryViewReader.read_int,
        uint.__name__: MemoryViewReader.read_u32,
        s24.__name__: MemoryViewReader.read_s24,
    }

    def __init__(self, reader: MemoryViewReader):
        for field in fields(self):
            setattr(self, field.name, self.readers[field.type](reader))

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment) -> Optional[int]:
        raise NotImplementedError(self)


T = TypeVar('T', bound=Instruction)
opcode_to_instruction: Dict[int, Type[T]] = {}


def instruction(opcode: int) -> Callable[[], Type[T]]:
    def wrapper(class_: Type[T]) -> Type[T]:
        assert opcode not in opcode_to_instruction, opcode_to_instruction[opcode]
        opcode_to_instruction[opcode] = class_
        return dataclass(init=False)(class_)
    return wrapper


# Instructions implementation.
# ----------------------------------------------------------------------------------------------------------------------

@instruction(160)
class Add(Instruction):
    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        value_2 = environment.operand_stack.pop()
        value_1 = environment.operand_stack.pop()
        environment.operand_stack.append(value_1 + value_2)


@instruction(197)
class AddInteger(Instruction):
    """
    Pop value1 and value2 off of the stack and convert them to int values using the ToInt32
    algorithm (ECMA-262 section 9.5). Add the two int values and push the result onto the
    stack.
    """

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        value_2 = environment.operand_stack.pop()
        value_1 = environment.operand_stack.pop()
        environment.operand_stack.append(int(value_1) + int(value_2))


@instruction(134)
class AsType(Instruction):
    index: u30


@instruction(135)
class AsTypeLate(Instruction):
    pass


@instruction(168)
class BitAnd(Instruction):
    pass


@instruction(151)
class BitNot(Instruction):
    pass


@instruction(169)
class BitOr(Instruction):
    pass


@instruction(170)
class BitXor(Instruction):
    pass


@instruction(65)
class Call(Instruction):
    arg_count: u30

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        args = [environment.operand_stack.pop() for i in range(self.arg_count)]
        args.reverse()
        receiver = environment.operand_stack.pop()
        function = environment.operand_stack.pop()
        return_value = function.call(receiver, args)
        environment.operand_stack.append(return_value)


@instruction(67)
class CallMethod(Instruction):
    index: u30
    arg_count: u30


@instruction(70)
class CallProperty(Instruction):
    index: u30
    arg_count: u30

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        args = [environment.operand_stack.pop() for i in range(self.arg_count)]
        args.reverse()

        multiname = machine.multinames[self.index]
        try:
            name, namespaces = machine.resolve_multiname_identifiers(environment.operand_stack, multiname)
            object = environment.operand_stack.pop()
            parent, name, namespace = machine.resolve_multiname(
                [object],
                name,
                namespaces
            )
        except KeyError:
            raise NotImplementedError('TypeError')
        else:
            return_value = parent.properties[namespace, name].call(object, args)
            environment.operand_stack.append(return_value)


@instruction(76)
class CallPropLex(Instruction):
    index: u30
    arg_count: u30


@instruction(79)
class CallPropVoid(Instruction):
    index: u30
    arg_count: u30


@instruction(68)
class CallStatic(Instruction):
    index: u30
    arg_count: u30


@instruction(69)
class CallSuper(Instruction):
    index: u30
    arg_count: u30


@instruction(78)
class CallSuperVoid(Instruction):
    index: u30
    arg_count: u30


@instruction(120)
class CheckFilter(Instruction):
    pass


@instruction(128)
class Coerce(Instruction):
    index: u30


@instruction(130)
class CoerceAny(Instruction):
    pass


@instruction(133)
class CoerceString(Instruction):
    pass


@instruction(66)
class Construct(Instruction):
    arg_count: u30

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        args = [environment.operand_stack.pop() for i in range(self.arg_count)]
        args.reverse()
        constructor = environment.operand_stack.pop()
        return_value = constructor.construct(args)
        environment.operand_stack.append(return_value)

@instruction(74)
class ConstructProp(Instruction):
    index: u30
    arg_count: u30


@instruction(73)
class ConstructSuper(Instruction):
    arg_count: u30

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        args = [environment.operand_stack.pop() for i in range(self.arg_count)]
        args.reverse()
        object = environment.operand_stack.pop()

        if object == None or object == undefined:
            raise NotImplementedError('TypeError')

        # TODO invoke the constructor on the base class of object with the given arguments


@instruction(118)
class ConvertToBoolean(Instruction):
    pass


@instruction(115)
class ConvertToInteger(Instruction):
    """
    `value` is popped off of the stack and converted to an integer. The result, `intvalue`, is pushed
    onto the stack. This uses the `ToInt32` algorithm, as described in ECMA-262 section 9.5, to
    perform the conversion.
    """

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.append(int(environment.operand_stack.pop()))


@instruction(117)
class ConvertToDouble(Instruction):
    """
    `value` is popped off of the stack and converted to a double. The result, `doublevalue`, is pushed
    onto the stack. This uses the `ToNumber` algorithm, as described in ECMA-262 section 9.3,
    to perform the conversion.
    """

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.append(float(environment.operand_stack.pop()))


@instruction(119)
class ConvertToObject(Instruction):
    pass


@instruction(116)
class ConvertToUnsignedInteger(Instruction):
    pass


@instruction(112)
class ConvertToString(Instruction):
    pass


@instruction(239)
class Debug(Instruction):
    debug_type: u8
    index: u30
    reg: u8
    extra: u30


@instruction(241)
class DebugFile(Instruction):
    index: u30


@instruction(240)
class DebugLine(Instruction):
    linenum: u30


@instruction(148)
class DecLocal(Instruction):
    index: u30


@instruction(195)
class DecLocalInteger(Instruction):
    index: u30


@instruction(147)
class Decrement(Instruction):
    pass


@instruction(193)
class DecrementInteger(Instruction):
    pass


@instruction(106)
class DeleteProperty(Instruction):
    index: u30


@instruction(163)
class Divide(Instruction):
    """
    Pop `value1` and `value2` off of the stack, convert `value1` and `value2` to `Number` to create
    `value1_number` and `value2_number`. Divide `value1_number` by `value2_number` and push the
    result onto the stack.
    """

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        value_2 = environment.operand_stack.pop()
        value_1 = environment.operand_stack.pop()
        environment.operand_stack.append(value_1 / value_2)


@instruction(42)
class Dup(Instruction):
    """
    Duplicates the top value of the stack, and then pushes the duplicated value onto the stack.
    """

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        value = environment.operand_stack.pop()
        environment.operand_stack.extend([value, value])


@instruction(6)
class DXNS(Instruction):
    index: u30


@instruction(7)
class DXNSLate(Instruction):
    pass


@instruction(171)
class EqualsOperation(Instruction):
    pass


@instruction(114)
class EscXAttr(Instruction):
    pass


@instruction(113)
class EscXElem(Instruction):
    pass


@instruction(94)
class FindProperty(Instruction):
    index: u30

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        multiname = machine.multinames[self.index]
        try:
            name, namespaces = machine.resolve_multiname_identifiers(environment.operand_stack, multiname)
            parent, _, _ = machine.resolve_multiname(
                [environment.registers[0]] + environment.scope_stack,
                name,
                namespaces
            )
        except KeyError:
            environment.operand_stack.append(machine.global_object)
        else:
            environment.operand_stack.append(parent)


@instruction(93)
class FindPropStrict(Instruction):
    """
    `index` is a `u30` that must be an index into the `multiname` constant pool. If the multiname at
    that index is a runtime multiname the name and/or namespace will also appear on the stack
    so that the multiname can be constructed correctly at runtime.

    This searches the scope stack, and then the saved scope in the method closure, for a property
    with the name specified by the multiname at `index`.

    If any of the objects searched is a `with` scope, its declared and dynamic properties will be
    searched for a match. Otherwise only the declared traits of a scope will be searched. The
    global object will have its declared traits, dynamic properties, and prototype chain searched.

    If the property is resolved then the object it was resolved in is pushed onto the stack. If the
    property is unresolved in all objects on the scope stack then an exception is thrown.

    A `ReferenceError` is thrown if the property is not resolved in any object on the scope stack.
    """

    index: u30

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        multiname = machine.multinames[self.index]
        try:
            name, namespaces = machine.resolve_multiname_identifiers(environment.operand_stack, multiname)
            parent, _, _ = machine.resolve_multiname(
                [environment.registers[0]] + environment.scope_stack,
                name,
                namespaces
            )
        except KeyError:
            raise NotImplementedError('ReferenceError')
        else:
            environment.operand_stack.append(parent)


@instruction(89)
class GetDescendants(Instruction):
    index: u30


@instruction(100)
class GetGlobalScope(Instruction):
    pass


@instruction(110)
class GetGlobalSlot(Instruction):
    slot_index: u30


@instruction(96)
class GetLex(Instruction):
    """
    `index` is a `u30` that must be an index into the multiname constant pool. The multiname at
    `index` must not be a runtime multiname, so there are never any optional namespace or name
    values on the stack.

    This is the equivalent of doing a `findpropstrict` followed by a `getproperty`. It will find the
    object on the scope stack that contains the property, and then will get the value from that
    object. See "Resolving multinames" on page 10.

    A `ReferenceError` is thrown if the property is unresolved in all of the objects on the scope
    stack.
    """

    index: u30

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        multiname = machine.multinames[self.index]
        try:
            name, namespaces = machine.resolve_multiname_identifiers(environment.operand_stack, multiname)
            parent, name, namespace = machine.resolve_multiname(
                [environment.registers[0]] + environment.scope_stack,
                name,
                namespaces
            )
        except KeyError:
            raise NotImplementedError('ReferenceError')
        else:
            value = machine.resolve_qname(parent, namespace, name)
            environment.operand_stack.append(value)


@instruction(98)
class GetLocal(Instruction):
    index: u30


@instruction(208)
class GetLocal0(Instruction):
    """
    `<n>` is the index of a local register. The value of that register is pushed onto the stack.
    """

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.append(environment.registers[0])


@instruction(209)
class GetLocal1(Instruction):
    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.append(environment.registers[1])


@instruction(210)
class GetLocal2(Instruction):
    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.append(environment.registers[2])


@instruction(211)
class GetLocal3(Instruction):
    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.append(environment.registers[3])


@instruction(102)
class GetProperty(Instruction):
    index: u30

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        multiname = machine.multinames[self.index]
        try:
            name, namespaces = machine.resolve_multiname_identifiers(environment.operand_stack, multiname)
            object = environment.operand_stack.pop()
            parent, name, namespace = machine.resolve_multiname(
                [object],
                name,
                namespaces
            )
        except KeyError:
            environment.operand_stack.append(undefined)
        else:
            value = machine.resolve_qname(parent, namespace, name)
            environment.operand_stack.append(value)


@instruction(101)
class GetScopeObject(Instruction):
    """
    `index` is an unsigned byte that specifies the index of the scope object to retrieve from the local
    scope stack. `index` must be less than the current depth of the scope stack. The scope at that
    `index` is retrieved and pushed onto the stack. The scope at the top of the stack is at index
    `scope_depth - 1`, and the scope at the bottom of the stack is index `0`.
    """

    index: u8

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.append(environment.scope_stack[self.index])


@instruction(108)
class GetSlot(Instruction):
    slot_index: u30


@instruction(4)
class GetSuper(Instruction):
    index: u30


@instruction(176)
class GreaterEquals(Instruction):
    """
    Pop `value1` and `value2` off of the stack. Compute `value1 < value2` using the Abstract
    Relational Comparison Algorithm, as described in ECMA-262 section 11.8.5. If the result of
    the comparison is `false`, push `true` onto the stack. Otherwise push `false` onto the stack.
    """

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        value_2 = environment.operand_stack.pop()
        value_1 = environment.operand_stack.pop()
        environment.operand_stack.append(value_1 >= value_2)


@instruction(175)
class GreaterThan(Instruction):
    pass


@instruction(31)
class HasNext(Instruction):
    pass


@instruction(50)
class HasNext2(Instruction):
    object_reg: uint
    index_reg: uint


@instruction(19)
class IfEq(Instruction):
    offset: s24


@instruction(18)
class IfFalse(Instruction):
    """
    Pop value off the stack and convert it to a `Boolean`. If the converted value is `false`, jump the
    number of bytes indicated by `offset`. Otherwise continue executing code from this point.
    """

    offset: s24

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        if not environment.operand_stack.pop():
            raise ASJumpException(self.offset)


@instruction(24)
class IfGE(Instruction):
    offset: s24


@instruction(23)
class IfGT(Instruction):
    offset: s24


@instruction(22)
class IfLE(Instruction):
    offset: s24


@instruction(21)
class IfLT(Instruction):
    """
    `offset` is an `s24` that is the number of bytes to jump if `value1` is less than `value2`.

    Compute value1 < value2 using the abstract relational comparison algorithm in ECMA-262
    section 11.8.5. If the result of the comparison is `true`, jump the number of bytes indicated
    by `offset`. Otherwise continue executing code from this point.
    """

    offset: s24

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        value_2 = environment.operand_stack.pop()
        value_1 = environment.operand_stack.pop()
        if value_1 < value_2:
            raise ASJumpException(self.offset)


@instruction(15)
class IfNGE(Instruction):
    offset: s24


@instruction(14)
class IfNGT(Instruction):
    """
    Compute `value2 < value1` using the abstract relational comparison algorithm in ECMA-262
    section 11.8.5. If the result of the comparison is not `true`, jump the number of bytes
    indicated by `offset`. Otherwise continue executing code from this point.
    """

    offset: s24

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        value_2 = environment.operand_stack.pop()
        value_1 = environment.operand_stack.pop()
        # FIXME: NaN.
        if not value_1 > value_2:
            raise ASJumpException(self.offset)


@instruction(13)
class IfNLE(Instruction):
    offset: s24


@instruction(12)
class IfNLT(Instruction):
    """
    Compute `value1 < value2` using the abstract relational comparison algorithm in ECMA-262
    section 11.8.5. If the result of the comparison is false, then jump the number of bytes
    indicated by `offset`. Otherwise continue executing code from this point.

    This appears to have the same effect as `ifge`, however, their handling of `NaN` is different. If
    either of the compared values is `NaN` then the comparison `value1 < value2` will return
    `undefined`. In that case `ifnlt` will branch (`undefined` is not true), but `ifge` will not
    branch.
    """

    offset: s24

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        value_2 = environment.operand_stack.pop()
        value_1 = environment.operand_stack.pop()
        # FIXME: NaN.
        if not value_1 < value_2:
            raise ASJumpException(self.offset)


@instruction(20)
class IfNE(Instruction):
    offset: s24


@instruction(25)
class IfStrictEq(Instruction):
    offset: s24


@instruction(26)
class IfStrictNE(Instruction):
    offset: s24


@instruction(17)
class IfTrue(Instruction):
    offset: s24


@instruction(180)
class In(Instruction):
    pass


@instruction(146)
class IncLocal(Instruction):
    index: u30


@instruction(194)
class IncLocalInteger(Instruction):
    index: u30


@instruction(145)
class Increment(Instruction):
    pass


@instruction(192)
class IncrementInteger(Instruction):
    pass


@instruction(104)
class InitProperty(Instruction):
    index: u30

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        multiname = machine.multinames[self.index]
        value = environment.operand_stack.pop()
        try:
            name, namespaces = machine.resolve_multiname_identifiers(environment.operand_stack, multiname)
            object = environment.operand_stack.pop()
            parent, name, namespace = machine.resolve_multiname(
                [object],
                name,
                namespaces
            )
        except KeyError:
            object.properties['', name] = value
        else:
            parent.properties[namespace, name] = value

@instruction(177)
class InstanceOf(Instruction):
    pass


@instruction(178)
class IsType(Instruction):
    index: u30


@instruction(179)
class IsTypeLate(Instruction):
    pass


@instruction(16)
class Jump(Instruction):
    offset: s24


@instruction(8)
class Kill(Instruction):
    index: u30

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.registers[self.index] = machine.get_constant(ConstantKind.UNDEFINED, 0)

@instruction(9)
class Label(Instruction):
    pass


@instruction(174)
class LessEquals(Instruction):
    pass


@instruction(173)
class LessThan(Instruction):
    pass


@instruction(27)
class LookupSwitch(Instruction):
    default_offset: s24
    case_offsets: Tuple[s24, ...]

    # noinspection PyMissingConstructor
    def __init__(self, reader: MemoryViewReader):
        self.default_offset = reader.read_s24()
        case_count = reader.read_int()
        self.case_offsets = read_array(reader, MemoryViewReader.read_s24, case_count + 1)


@instruction(165)
class LeftShift(Instruction):
    pass


@instruction(164)
class Modulo(Instruction):
    pass


@instruction(162)
class Multiply(Instruction):
    pass


@instruction(199)
class MultiplyInteger(Instruction):
    pass


@instruction(144)
class Negate(Instruction):
    pass


@instruction(196)
class NegateInteger(Instruction):
    pass


@instruction(87)
class NewActivation(Instruction):
    pass


@instruction(86)
class NewArray(Instruction):
    arg_count: u30


@instruction(90)
class NewCatch(Instruction):
    index: u30


@instruction(88)
class NewClass(Instruction):
    index: u30


    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        base_type = environment.operand_stack.pop()

        if self.index in machine.class_objects:
            class_object = machine.class_objects[self.index]
        else:
            class_object = ASObject()
            class_object.base_type = base_type
            machine.class_objects[self.index] = class_object

            for trait in machine.abc_file.classes[self.index].traits:
                if trait.kind == TraitKind.CONST:
                    multiname = machine.multinames[trait.name_index]
                    class_object.properties[None,
                                            machine.strings[multiname.name_index]] = ASObject()

        environment.operand_stack.append(class_object)
        machine.call_method(
            machine.abc_file.classes[self.index].init_index, class_object)


@instruction(64)
class NewFunction(Instruction):
    index: u30


@instruction(85)
class NewObject(Instruction):
    arg_count: u30


@instruction(30)
class NextName(Instruction):
    pass


@instruction(35)
class NextValue(Instruction):
    pass


@instruction(2)
class Nop(Instruction):
    pass


@instruction(150)
class Not(Instruction):
    pass


@instruction(41)
class Pop(Instruction):
    """
    Pops the top value from the stack and discards it.
    """

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.pop()


@instruction(29)
class PopScope(Instruction):
    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.scope_stack.pop()


@instruction(36)
class PushByte(Instruction):
    byte_value: u8

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.append(self.byte_value)


@instruction(47)
class PushDouble(Instruction):
    """
    `index` is a `u30` that must be an index into the `double` constant pool. The double value at
    `index` in the `double` constant pool is pushed onto the stack.
    """

    index: u30

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.append(machine.doubles[self.index])


@instruction(39)
class PushFalse(Instruction):
    """
    Push the false value onto the stack.
    """

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.append(False)


@instruction(45)
class PushInteger(Instruction):
    """
    `index` is a `u30` that must be an index into the `integer` constant pool. The int value at `index` in
    the integer constant pool is pushed onto the stack.
    """

    index: u30

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.append(machine.integers[self.index])


@instruction(49)
class PushNamespace(Instruction):
    index: u30


@instruction(40)
class PushNaN(Instruction):
    pass


@instruction(32)
class PushNull(Instruction):
    pass

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.append(machine.get_constant(ConstantKind.NULL, 0))

@instruction(48)
class PushScope(Instruction):
    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        value = environment.operand_stack.pop()
        assert value is not None and value is not undefined
        environment.scope_stack.append(value)


@instruction(37)
class PushShort(Instruction):
    value: u30


@instruction(44)
class PushString(Instruction):
    index: u30

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.append(ASString(machine.strings[self.index]))

@instruction(38)
class PushTrue(Instruction):
    """
    Push the `true` value onto the stack.
    """

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.operand_stack.append(True)


@instruction(46)
class PushUnsignedInteger(Instruction):
    index: u30


@instruction(33)
class PushUndefined(Instruction):
    pass


@instruction(28)
class PushWith(Instruction):
    pass


@instruction(72)
class ReturnValue(Instruction):
    """
    Return from the currently executing method. This returns the top value on the stack.
    `return_value` is popped off of the stack, and coerced to the expected return type of the
    method. The coerced value is what is actually returned from the method.

    A `TypeError` is thrown if `return_value` cannot be coerced to the expected return type of the
    executing method.
    """

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        # FIXME: coerce to the expected return type.
        raise ASReturnException(environment.operand_stack.pop())


@instruction(71)
class ReturnVoid(Instruction):
    """
    Return from the currently executing method. This returns the value `undefined`. If the
    method has a return type, then undefined is coerced to that type and then returned.
    """

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        raise ASReturnException(undefined)


@instruction(166)
class RightShift(Instruction):
    pass


@instruction(99)
class SetLocal(Instruction):
    index: u30


@instruction(212)
class SetLocal0(Instruction):
    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.registers[0] = environment.operand_stack.pop()


@instruction(213)
class SetLocal1(Instruction):
    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.registers[1] = environment.operand_stack.pop()


@instruction(214)
class SetLocal2(Instruction):
    """
    `<n>` is an index of a local register. The register at that index is set to value, and value is
    popped off the stack.
    """

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.registers[2] = environment.operand_stack.pop()


@instruction(215)
class SetLocal3(Instruction):
    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        environment.registers[3] = environment.operand_stack.pop()


@instruction(111)
class SetGlobalSlot(Instruction):
    slot_index: u30


@instruction(97)
class SetProperty(Instruction):
    index: u30


@instruction(109)
class SetSlot(Instruction):
    slot_index: u30


@instruction(5)
class SetSuper(Instruction):
    index: u30


@instruction(172)
class StrictEquals(Instruction):
    pass


@instruction(161)
class Subtract(Instruction):
    pass


@instruction(198)
class SubtractInteger(Instruction):
    """
    Pop `value1` and `value2` off of the stack and convert `value1` and `value2` to int to create
    `value1_int` and `value2_int`. Subtract `value2_int` from `value1_int`. Push the result onto the
    stack.
    """

    def execute(self, machine: avm2.vm.VirtualMachine, environment: avm2.vm.MethodEnvironment):
        value_2 = environment.operand_stack.pop()
        value_1 = environment.operand_stack.pop()
        environment.operand_stack.append(int(value_1) - int(value_2))


@instruction(43)
class Swap(Instruction):
    pass


@instruction(3)
class Throw(Instruction):
    pass


@instruction(149)
class TypeOf(Instruction):
    pass


@instruction(167)
class UnsignedRightShift(Instruction):
    pass
