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

from gzip import compress, decompress
from io import BytesIO
from struct import pack
from typing import cast, Any

from .primitives.bytes import Bytes
from .tl_object import TLObject

_ID_BYTES = pack("<I", 0x3072CFA1)


class GzipPacked(TLObject):
    ID = 0x3072CFA1

    __slots__: tuple = ("packed_data",)

    QUALNAME = "GzipPacked"

    def __init__(self, packed_data: TLObject):
        self.packed_data = packed_data

    @staticmethod
    def read(data: BytesIO, *args: Any) -> "GzipPacked":
        return cast(GzipPacked, TLObject.read(
            BytesIO(decompress(Bytes.read(data)))
        ))

    def _write_to(self, b: BytesIO) -> None:
        b.write(_ID_BYTES)
        Bytes.write_to(compress(self.packed_data.write()), b)
