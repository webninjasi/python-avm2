from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, ClassVar

from avm2.abc.types import ABCClassIndex

undefined = None

@dataclass
class ASObject:
    class_index: Optional[ABCClassIndex] = None
    properties: Dict[Tuple[str, str], ASObject] = field(default_factory=dict)

    def get_property(self, namespace: str, name: str) -> ASObject:
        return self.properties[namespace, name]


@dataclass
class ASUndefined(ASObject):
    pass


undefined = ASUndefined()


@dataclass
class ASString(ASObject):
    properties: ClassVar[Dict[Tuple[str, str], ASObject]] = {}
    value: str = field(default='')

    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def get_property(self, namespace: str, name: Any) -> ASObject:
        # TODO check namespace?
        if isinstance(name, int) and 0 <= name < len(self.value):
            return self.value[name]
        return ASString.properties[namespace, name]


@dataclass
class ASArray(ASObject):
    properties: ClassVar[Dict[Tuple[str, str], ASObject]] = {}
    value: str = field(default='')

    def __init__(self, value: list[Any]):
        super().__init__()
        self.value = value

    def get_property(self, namespace: str, name: Any) -> ASObject:
        # TODO check namespace?
        if isinstance(name, int) and 0 <= name < len(self.value):
            return self.value[name]
        return super().get_property(namespace, name)
