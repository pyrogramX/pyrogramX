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

from importlib import import_module
from io import BytesIO
from json import dumps
from struct import unpack
from typing import cast, Any, Union

from ..all import objects


class TLObject:
    __slots__: tuple = ()

    QUALNAME = "Base"

    @classmethod
    def read(cls, b: BytesIO, *args: Any) -> Any:
        constructor_id = unpack("<I", b.read(4))[0]

        entry = objects[constructor_id]
        if isinstance(entry, str):
            path, name = entry.rsplit(".", 1)
            entry = getattr(import_module(path), name)
            objects[constructor_id] = entry

        return cast(TLObject, entry).read(b, *args)

    def write(self, *args: Any) -> bytes:
        b = BytesIO()
        self._write_to(b)
        return b.getvalue()

    def _write_to(self, b: BytesIO) -> None:
        pass

    @staticmethod
    def default(obj: "TLObject") -> Union[str, dict[str, str]]:
        if isinstance(obj, bytes):
            return repr(obj)

        return {
            "_": obj.QUALNAME,
            **{
                attr: (value := getattr(obj, attr))
                for attr in obj.__slots__
                if (value := getattr(obj, attr)) is not None
            }
        }

    def __str__(self) -> str:
        return dumps(self, indent=4, default=TLObject.default, ensure_ascii=False)

    def __repr__(self) -> str:
        if not hasattr(self, "QUALNAME"):
            return repr(self)

        return "pyrogramX.raw.{}({})".format(
            self.QUALNAME,
            ", ".join(
                f"{attr}={repr(getattr(self, attr))}"
                for attr in self.__slots__
                if getattr(self, attr) is not None
            )
        )

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return False

        for attr in self.__slots__:
            try:
                if getattr(self, attr) != getattr(other, attr):
                    return False
            except AttributeError:
                return False

        return True

    def __len__(self) -> int:
        return len(self.write())

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        pass
