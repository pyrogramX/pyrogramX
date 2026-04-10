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


class Int(bytes, TLObject):
    SIZE = 4
    _SIGNED_FMT = "<i"
    _UNSIGNED_FMT = "<I"

    @classmethod
    def read(cls, data: BytesIO, signed: bool = True, *args: Any) -> int:
        return unpack(cls._SIGNED_FMT if signed else cls._UNSIGNED_FMT, data.read(cls.SIZE))[0]

    def __new__(cls, value: int, signed: bool = True) -> bytes:
        return pack(cls._SIGNED_FMT if signed else cls._UNSIGNED_FMT, value)

    @classmethod
    def write_to(cls, value: int, b: BytesIO, signed: bool = True) -> None:
        b.write(pack(cls._SIGNED_FMT if signed else cls._UNSIGNED_FMT, value))


class Long(Int):
    SIZE = 8
    _SIGNED_FMT = "<q"
    _UNSIGNED_FMT = "<Q"


class Int128(bytes, TLObject):
    SIZE = 16

    @classmethod
    def read(cls, data: BytesIO, signed: bool = True, *args: Any) -> int:
        return int.from_bytes(data.read(cls.SIZE), "little", signed=signed)

    def __new__(cls, value: int, signed: bool = True) -> bytes:
        return value.to_bytes(cls.SIZE, "little", signed=signed)

    @classmethod
    def write_to(cls, value: int, b: BytesIO, signed: bool = True) -> None:
        b.write(value.to_bytes(cls.SIZE, "little", signed=signed))


class Int256(Int128):
    SIZE = 32
