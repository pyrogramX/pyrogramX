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

from .int import Int, Long
from ..list import List
from ..tl_object import TLObject

_VECTOR_ID_BYTES = pack("<I", 0x1CB5C415)


class Vector(bytes, TLObject):
    ID = 0x1CB5C415

    @staticmethod
    def read_bare(b: BytesIO, size: int) -> Any:
        if size == 4:
            return Int.read(b)
        if size == 8:
            return Long.read(b)
        return TLObject.read(b)

    @classmethod
    def read(cls, data: BytesIO, t: Any = None, *args: Any) -> List:
        count = Int.read(data)
        left = data.getbuffer().nbytes - data.tell()
        size = (left / count) if count else 0

        return List(
            t.read(data) if t
            else Vector.read_bare(data, size)
            for _ in range(count)
        )

    def __new__(cls, value: list, t: Any = None) -> bytes:
        b = BytesIO()
        cls.write_to(value, b, t)
        return b.getvalue()

    @classmethod
    def write_to(cls, value: list, b: BytesIO, t: Any = None) -> None:
        b.write(_VECTOR_ID_BYTES)
        b.write(pack("<i", len(value)))

        if t:
            for item in value:
                b.write(t(item))
        else:
            for item in value:
                item._write_to(b)
