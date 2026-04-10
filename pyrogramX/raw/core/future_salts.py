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

from .future_salt import FutureSalt
from .primitives.int import Int, Long
from .tl_object import TLObject

_ID_BYTES = pack("<I", 0xAE500895)


class FutureSalts(TLObject):
    ID = 0xAE500895

    __slots__: tuple = ("req_msg_id", "now", "salts")

    QUALNAME = "FutureSalts"

    def __init__(self, req_msg_id: int, now: int, salts: list[FutureSalt]):
        self.req_msg_id = req_msg_id
        self.now = now
        self.salts = salts

    @staticmethod
    def read(data: BytesIO, *args: Any) -> "FutureSalts":
        req_msg_id = Long.read(data)
        now = Int.read(data)

        count = Int.read(data)
        salts = [FutureSalt.read(data) for _ in range(count)]

        return FutureSalts(req_msg_id, now, salts)

    def _write_to(self, b: BytesIO) -> None:
        b.write(_ID_BYTES)
        b.write(pack("<qi", self.req_msg_id, self.now))
        b.write(pack("<i", len(self.salts)))

        for salt in self.salts:
            salt._write_to(b)
