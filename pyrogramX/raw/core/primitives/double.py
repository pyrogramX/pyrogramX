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


class Double(bytes, TLObject):
    @classmethod
    def read(cls, data: BytesIO, *args: Any) -> float:
        return unpack("<d", data.read(8))[0]

    def __new__(cls, value: float) -> bytes:
        return pack("<d", value)

    @classmethod
    def write_to(cls, value: float, b: BytesIO) -> None:
        b.write(pack("<d", value))
