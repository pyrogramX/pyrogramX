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

from .message import Message
from .primitives.int import Int
from .tl_object import TLObject

_ID_BYTES = pack("<I", 0x73F1F8DC)


class MsgContainer(TLObject):
    ID = 0x73F1F8DC

    __slots__: tuple = ("messages",)

    QUALNAME = "MsgContainer"

    def __init__(self, messages: list[Message]):
        self.messages = messages

    @staticmethod
    def read(data: BytesIO, *args: Any) -> "MsgContainer":
        count = Int.read(data)
        return MsgContainer([Message.read(data) for _ in range(count)])

    def _write_to(self, b: BytesIO) -> None:
        b.write(_ID_BYTES)
        b.write(pack("<i", len(self.messages)))

        for message in self.messages:
            message._write_to(b)
