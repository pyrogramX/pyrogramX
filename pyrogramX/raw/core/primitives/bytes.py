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
from struct import pack
from typing import Any

from ..tl_object import TLObject

_PAD = [b"", b"\x00", b"\x00\x00", b"\x00\x00\x00"]


class Bytes(bytes, TLObject):
    @classmethod
    def read(cls, data: BytesIO, *args: Any) -> bytes:
        length = data.read(1)[0]

        if length <= 253:
            x = data.read(length)
            data.read(-(length + 1) % 4)
        else:
            length = int.from_bytes(data.read(3), "little")
            x = data.read(length)
            data.read(-length % 4)

        return x

    def __new__(cls, value: bytes) -> bytes:
        length = len(value)

        if length <= 253:
            return (
                pack("B", length)
                + value
                + _PAD[-(length + 1) % 4]
            )
        else:
            return (
                b"\xfe"
                + length.to_bytes(3, "little")
                + value
                + _PAD[-length % 4]
            )

    @classmethod
    def write_to(cls, value: bytes, b: BytesIO) -> None:
        length = len(value)

        if length <= 253:
            b.write(pack("B", length))
            b.write(value)
            pad = -(length + 1) % 4
        else:
            b.write(b"\xfe")
            b.write(length.to_bytes(3, "little"))
            b.write(value)
            pad = -length % 4

        if pad:
            b.write(_PAD[pad])
