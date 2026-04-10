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

import re
import logging
import asyncio
from datetime import datetime

import aiofiles

log = logging.getLogger(__name__)

_RE_DIGITS = re.compile(r"_\d+")
_RE_EXTRACT = re.compile(r"_(\d+)")

_exceptions = None


def _get_exceptions():
    global _exceptions
    if _exceptions is None:
        from .exceptions.all import exceptions
        _exceptions = exceptions
    return _exceptions


class RPCError(Exception):
    ID = None
    CODE = None
    NAME = None
    MESSAGE = "{value}"
    __slots__ = ("value",)

    def __init__(
        self,
        value: int | str | "raw.types.RpcError" = None,
        rpc_name: str = None,
        is_unknown: bool = False,
        is_signed: bool = False
    ):
        super().__init__("Telegram says: [{}{} {}] - {} {}".format(
            "-" if is_signed else "",
            self.CODE,
            self.ID or self.NAME,
            self.MESSAGE.format(value=value),
            f'(caused by "{rpc_name}")' if rpc_name else ""
        ))

        try:
            self.value = int(value)
        except (ValueError, TypeError):
            self.value = value

        if is_unknown:
            self._log_unknown(value, rpc_name)

    @staticmethod
    def _log_unknown(value, rpc_name):
        log.warning("Unknown RPC error: %s (caused by %s)", value, rpc_name)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        async def _write():
            async with aiofiles.open("unknown_errors.txt", "a") as f:
                await f.write(f"{datetime.now()}\t{value}\t{rpc_name}\n")

        loop.create_task(_write())

    @staticmethod
    def raise_it(rpc_error, rpc_type):
        exceptions = _get_exceptions()
        error_code = rpc_error.error_code
        is_signed = error_code < 0
        error_message = rpc_error.error_message
        rpc_name = ".".join(rpc_type.QUALNAME.split(".")[1:])

        if is_signed:
            error_code = -error_code

        if error_code not in exceptions:
            raise UnknownError(
                value=f"[{error_code} {error_message}]",
                rpc_name=rpc_name,
                is_unknown=True,
                is_signed=is_signed
            )

        error_id = _RE_DIGITS.sub("_X", error_message)
        code_exceptions = exceptions[error_code]

        if error_id not in code_exceptions:
            raise code_exceptions["_"](
                value=f"[{error_code} {error_message}]",
                rpc_name=rpc_name,
                is_unknown=True,
                is_signed=is_signed
            )

        value = _RE_EXTRACT.search(error_message)
        value = value.group(1) if value is not None else value

        raise code_exceptions[error_id](
            value=value,
            rpc_name=rpc_name,
            is_unknown=False,
            is_signed=is_signed
        )


class UnknownError(RPCError):
    __slots__ = ()
    CODE = 520
    """:obj:`int`: Error code"""
    NAME = "Unknown error"
