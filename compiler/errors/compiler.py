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

import csv
import hashlib
import os
import re
import shutil
from pathlib import Path

HOME = "compiler/errors"
DEST = "pyrogramX/errors/exceptions"
NOTICE_PATH = "NOTICE"


def snek(s):
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def caml(s):
    s = snek(s).split("_")
    return "".join([str(i.title()) for i in s])


def start(force: bool = False):
    # Incremental compilation: skip if source TSVs haven't changed
    source_dir = Path(f"{HOME}/source")
    hash_file = Path(DEST) / ".source_hash"

    hasher = hashlib.sha256()
    for tsv in sorted(source_dir.glob("*.tsv")):
        hasher.update(tsv.read_bytes())
    current_hash = hasher.hexdigest()

    if not force and hash_file.exists() and hash_file.read_text().strip() == current_hash:
        print("Error sources unchanged, skipping compilation")
        return

    shutil.rmtree(DEST, ignore_errors=True)
    os.makedirs(DEST)

    files = sorted(os.listdir(f"{HOME}/source"))

    with open(NOTICE_PATH, encoding="utf-8") as f:
        notice = []
        for line in f.readlines():
            notice.append(f"# {line}".strip())
        notice = "\n".join(notice)

    # Collect data for all.py generation
    all_imports = []  # (module_name, class_names)
    all_entries = []  # (code, entries) where entries = [("_", SuperClass), (error_id, SubClass), ...]

    with open(f"{DEST}/__init__.py", "w", encoding="utf-8") as f_init:
        f_init.write(notice + "\n\n")

    count = 0

    for i in files:
        if not i.endswith(".tsv"):
            continue

        match = re.search(r"(\d+)_([A-Z_]+)", i)
        if not match:
            continue

        code, name = match.groups()
        super_class = caml(name)
        module_name = f"{name.lower()}_{code}"
        display_name = " ".join(
            word.capitalize()
            for word in name.replace("_", " ").lower().split()
        )

        with open(f"{DEST}/__init__.py", "a", encoding="utf-8") as f_init:
            f_init.write(f"from .{module_name} import *\n")

        sub_classes = []
        class_names = [super_class]
        entries = [("_", super_class)]

        with open(f"{HOME}/source/{i}", encoding="utf-8") as f_csv:
            reader = csv.reader(f_csv, delimiter="\t")

            for j, row in enumerate(reader):
                if j == 0:
                    continue

                if not row:
                    continue

                count += 1
                error_id, error_message = row

                sub_class = caml(re.sub(r"_X", "_", error_id))
                sub_class = re.sub(r"^2", "Two", sub_class)
                sub_class = re.sub(r" ", "", sub_class)

                sub_classes.append((sub_class, error_id, error_message))
                class_names.append(sub_class)
                entries.append((error_id, sub_class))

        with open(f"{HOME}/template/class.txt", "r", encoding="utf-8") as f_tpl:
            class_template = f_tpl.read()

        with open(f"{HOME}/template/sub_class.txt", "r", encoding="utf-8") as f_tpl:
            sub_class_template = f_tpl.read()

        class_content = class_template.format(
            notice=notice,
            super_class=super_class,
            code=code,
            docstring=f'"""{display_name}"""',
            sub_classes="".join(
                sub_class_template.format(
                    sub_class=k[0],
                    super_class=super_class,
                    id=f'"{k[1]}"',
                    docstring=f'"""{k[2]}"""'
                )
                for k in sub_classes
            )
        )

        with open(f"{DEST}/{module_name}.py", "w", encoding="utf-8") as f_class:
            f_class.write(class_content)

        all_imports.append((module_name, class_names))
        all_entries.append((int(code), entries))

    # Generate all.py with direct class references
    with open(f"{DEST}/all.py", "w", encoding="utf-8") as f_all:
        f_all.write(notice + "\n\n")

        # Import all classes via wildcard
        for module_name, class_names in all_imports:
            f_all.write(f"from .{module_name} import *\n")

        f_all.write(f"\ncount = {count}\n\n")
        f_all.write("exceptions = {\n")

        for code, entries in all_entries:
            f_all.write(f"    {code}: {{\n")
            for error_id, class_name in entries:
                f_all.write(f'        "{error_id}": {class_name},\n')
            f_all.write("    },\n")

        f_all.write("}\n")

    # Save hash for incremental compilation
    hash_file.parent.mkdir(parents=True, exist_ok=True)
    hash_file.write_text(current_hash)

    print(f"Compiled {count} errors across {len(all_entries)} categories")


if __name__ == "__main__":
    HOME = "."
    DEST = "../../pyrogramX/errors/exceptions"
    NOTICE_PATH = "../../NOTICE"
    start()
