# PyrogramX - Telegram MTProto API Client Library for Python
# Copyright (C) 2026-present SychO <https://github.com/pyrogramX>

# This file is part of PyrogramX.

# PyrogramX is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# PyrogramX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with PyrogramX.  If not, see <http://www.gnu.org/licenses/>.

from io import BytesIO
from struct import pack, unpack
from typing import Any

from ..tl_object import TLObject

_TRUE_BYTES = pack("<I", 0x997275B5)
_FALSE_BYTES = pack("<I", 0xBC799737)


class BoolFalse(bytes, TLObject):
    ID = 0xBC799737
    value = False

    @classmethod
    def read(cls, *args: Any) -> bool:
        return cls.value

    def __new__(cls) -> bytes:
        return _FALSE_BYTES


class BoolTrue(BoolFalse):
    ID = 0x997275B5
    value = True

    def __new__(cls) -> bytes:
        return _TRUE_BYTES


class Bool(bytes, TLObject):
    @classmethod
    def read(cls, data: BytesIO, *args: Any) -> bool:
        return unpack("<I", data.read(4))[0] == BoolTrue.ID

    def __new__(cls, value: bool) -> bytes:
        return _TRUE_BYTES if value else _FALSE_BYTES

    @classmethod
    def write_to(cls, value: bool, b: BytesIO) -> None:
        b.write(_TRUE_BYTES if value else _FALSE_BYTES)
