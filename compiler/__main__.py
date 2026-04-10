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

import argparse
import time
from concurrent.futures import ThreadPoolExecutor

from compiler.api.compiler import start as start_api
from compiler.errors.compiler import start as start_errors


def main():
    parser = argparse.ArgumentParser(description="PyrogramX code generator")
    parser.add_argument("--force", action="store_true", help="force full recompilation")
    args = parser.parse_args()

    t0 = time.perf_counter()

    with ThreadPoolExecutor(max_workers=2) as pool:
        api_future = pool.submit(start_api, force=args.force)
        err_future = pool.submit(start_errors, force=args.force)

        api_future.result()
        err_future.result()

    elapsed = time.perf_counter() - t0
    print(f"Done in {elapsed:.2f}s")


main()
