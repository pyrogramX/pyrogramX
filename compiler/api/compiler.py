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

import os
import re
import shutil
import hashlib
from functools import partial
from pathlib import Path
from typing import NamedTuple

HOME_PATH = Path("compiler")
DESTINATION_PATH = Path("pyrogramX/raw")
NOTICE_PATH = Path("NOTICE")

SECTION_RE = re.compile(r"---(\w+)---")
LAYER_RE = re.compile(r"//\s*LAYER\s+(\d+)")
COMBINATOR_RE = re.compile(r"^([\w.]+)#([0-9a-f]+)\s(?:.*)=\s([\w<>.]+);$", re.MULTILINE)
ARGS_RE = re.compile(r"[^{](\w+):([\w?!.<>#]+)")
FLAGS_RE = re.compile(r"flags(\d?)\.(\d+)\?")
FLAGS_RE_2 = re.compile(r"flags(\d?)\.(\d+)\?([\w<>.]+)")
FLAGS_RE_3 = re.compile(r"flags(\d?):#")
INT_RE = re.compile(r"int(\d+)")

CORE_TYPES = ["int", "long", "int128", "int256", "double", "bytes", "string", "Bool", "true"]

# Python reserved keywords that may appear as TL arg names
RESERVED_KEYWORDS = {
    "self": "is_self",
    "from": "from_peer",
    "type": "type_",
    "filter": "filter_",
    "id": "id_",
    "hash": "hash_",
    "format": "format_",
    "in": "in_",
    "class": "class_",
    "import": "import_",
    "global": "global_",
    "return": "return_",
    "del": "del_",
    "pass": "pass_",
    "raise": "raise_",
}

# Only rename truly reserved keywords that cause SyntaxError
SYNTAX_RESERVED = {"self", "from", "in", "class", "import", "global", "return", "del", "pass", "raise"}

# Constructor IDs to skip (hand-written in core/)
SKIP_IDS = {
    0xBC799737,  # boolFalse
    0x997275B5,  # boolTrue
    0x3FEDD339,  # true
    0x1CB5C415,  # vector
    0x73F1F8DC,  # msg_container
    0x5BB8E511,  # message
    0x3072CFA1,  # gzip_packed
    0x0949D9DC,  # future_salt
    0xAE500895,  # future_salts
}

WARNING = """
# # # # # # # # # # # # # # # # # # # # # # # #
#               !!! WARNING !!!               #
#          This is a generated file!          #
# All changes made in this file will be lost! #
# # # # # # # # # # # # # # # # # # # # # # # #
""".strip()

COMBINATOR_TMPL = """{notice}

from io import BytesIO
from struct import pack, unpack

from pyrogramX.raw.core.primitives import Int, Long, Int128, Int256, Bool, Bytes, String, Double, Vector
from pyrogramX.raw.core.primitives.bool import _TRUE_BYTES, _FALSE_BYTES
from pyrogramX.raw.core import TLObject
from pyrogramX import raw
from typing import Optional, Any

{warning}


class {name}(TLObject):  # type: ignore
    \"\"\"{docstring}
    \"\"\"

    __slots__: tuple = ({slots})

    ID = {id}
    QUALNAME = "{qualname}"

    _ID_BYTES = pack("<I", {id})

    def __init__(self{arguments}) -> None:
        {fields}

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "{name}":
        {read_types}
        return {name}({return_arguments})

    def write(self, *args) -> bytes:
        b = BytesIO()
        self._write_to(b)
        return b.getvalue()

    def _write_to(self, b: BytesIO) -> None:
        b.write(self._ID_BYTES)
        {write_types}
"""

TYPE_TMPL = """{notice}

{warning}

from typing import Union
from pyrogramX import raw
from pyrogramX.raw.core import TLObject

{name} = Union[{types}]


# noinspection PyRedeclaration
class {name}:  # type: ignore
    \"\"\"{docstring}
    \"\"\"

    QUALNAME = "pyrogramX.raw.base.{qualname}"

    def __init__(self):
        raise TypeError(
            "Base types can only be used for type checking purposes: "
            "you tried to use a base type instance as argument, "
            "but you need to instantiate one of its constructors instead. "
            "More info: https://docs.pyrogram.org/telegram/base/{doc_name}"
        )
"""

# Optimized write patterns for _write_to
WRITE_CORE = {
    "int": 'b.write(pack("<i", self.{name}))',
    "long": 'b.write(pack("<q", self.{name}))',
    "double": 'b.write(pack("<d", self.{name}))',
    "string": "String.write_to(self.{name}, b)",
    "bytes": "Bytes.write_to(self.{name}, b)",
    "Bool": "b.write(_TRUE_BYTES if self.{name} else _FALSE_BYTES)",
    "int128": "Int128.write_to(self.{name}, b)",
    "int256": "Int256.write_to(self.{name}, b)",
}

# Optimized read patterns for struct.unpack
READ_CORE = {
    "int": 'unpack("<i", b.read(4))[0]',
    "long": 'unpack("<q", b.read(8))[0]',
    "double": 'unpack("<d", b.read(8))[0]',
    "string": "String.read(b)",
    "bytes": "Bytes.read(b)",
    "Bool": "Bool.read(b)",
    "int128": "int.from_bytes(b.read(16), 'little')",
    "int256": "int.from_bytes(b.read(32), 'little')",
}

# noinspection PyShadowingBuiltins
open = partial(open, encoding="utf-8")


class Combinator(NamedTuple):
    section: str
    qualname: str
    namespace: str
    name: str
    id: str
    has_flags: bool
    args: list[tuple[str, str]]
    qualtype: str
    typespace: str
    type: str


def snake(s: str):
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def camel(s: str):
    return "".join([i[0].upper() + i[1:] for i in s.split("_")])


def get_type_hint(type: str) -> str:
    is_flag = FLAGS_RE.match(type)
    is_core = False

    if is_flag:
        type = type.split("?")[1]

    if type in CORE_TYPES:
        is_core = True

        if type == "long" or "int" in type:
            type = "int"
        elif type == "double":
            type = "float"
        elif type == "string":
            type = "str"
        elif type in ["Bool", "true"]:
            type = "bool"
        else:
            type = "bytes"

    if type in ["Object", "!X"]:
        return "TLObject"

    if re.match("^vector", type, re.I):
        is_core = True
        sub_type = type.split("<")[1][:-1]
        type = f"list[{get_type_hint(sub_type)}]"

    if is_core:
        return f"Optional[{type}] = None" if is_flag else type
    else:
        ns, name = type.split(".") if "." in type else ("", type)
        type = f'"raw.base.' + ".".join([ns, name]).strip(".") + '"'
        return f'{type}{" = None" if is_flag else ""}'


def sort_args(args):
    args = args.copy()
    flags = [i for i in args if FLAGS_RE.match(i[1])]

    for i in flags:
        args.remove(i)

    for i in args[:]:
        if re.match(r"flags\d?", i[0]) and i[1] == "#":
            args.remove(i)

    return args + flags


def remove_whitespaces(source: str) -> str:
    lines = source.split("\n")
    for i, _ in enumerate(lines):
        if re.match(r"^\s+$", lines[i]):
            lines[i] = ""
    return "\n".join(lines)


def get_docstring_arg_type(t: str):
    if t in CORE_TYPES:
        if t == "long":
            return "``int`` ``64-bit``"
        elif "int" in t:
            size = INT_RE.match(t)
            return f"``int`` ``{size.group(1)}-bit``" if size else "``int`` ``32-bit``"
        elif t == "double":
            return "``float`` ``64-bit``"
        elif t == "string":
            return "``str``"
        elif t == "true":
            return "``bool``"
        else:
            return f"``{t.lower()}``"
    elif t == "TLObject" or t == "X":
        return "Any object from :obj:`~pyrogramX.raw.types`"
    elif t == "!X":
        return "Any function from :obj:`~pyrogramX.raw.functions`"
    elif t.lower().startswith("vector"):
        return "List of " + get_docstring_arg_type(t.split("<", 1)[1][:-1])
    else:
        return f":obj:`{t} <pyrogramX.raw.base.{t}>`"


def start(force: bool = False):
    # Incremental compilation: skip if schema hasn't changed
    schema_files = [HOME_PATH / "scheme/api.tl", HOME_PATH / "scheme/mtproto.tl"]
    hash_file = DESTINATION_PATH / ".schema_hash"

    hasher = hashlib.sha256()
    for sf in schema_files:
        hasher.update(sf.read_bytes())
    current_hash = hasher.hexdigest()

    if not force and hash_file.exists() and hash_file.read_text().strip() == current_hash:
        print("API schema unchanged, skipping compilation")
        return

    shutil.rmtree(DESTINATION_PATH / "types", ignore_errors=True)
    shutil.rmtree(DESTINATION_PATH / "functions", ignore_errors=True)
    shutil.rmtree(DESTINATION_PATH / "base", ignore_errors=True)

    with open(HOME_PATH / "scheme/api.tl") as f1, \
        open(HOME_PATH / "scheme/mtproto.tl") as f2:
        schema = (f1.read() + f2.read()).splitlines()

    with open(NOTICE_PATH, encoding="utf-8") as f:
        notice = []
        for line in f.readlines():
            notice.append(f"#  {line}".strip())
        notice = "\n".join(notice)

    types_to_constructors = {}
    types_to_functions = {}
    constructors_to_functions = {}
    namespaces_to_types = {}
    namespaces_to_constructors = {}
    namespaces_to_functions = {}

    section = "types"  # Default; schema may have types before first ---types--- marker
    layer = None
    combinators = []

    for line in schema:
        section_match = SECTION_RE.match(line)
        if section_match:
            section = section_match.group(1)
            continue

        layer_match = LAYER_RE.match(line)
        if layer_match:
            layer = layer_match.group(1)
            continue

        combinator_match = COMBINATOR_RE.match(line)
        if combinator_match:
            qualname, id_hex, qualtype = combinator_match.groups()

            # Skip core types handled manually
            if int(id_hex, 16) in SKIP_IDS:
                continue

            namespace, name = qualname.split(".") if "." in qualname else ("", qualname)
            name = camel(name)
            qualname = ".".join([namespace, name]).lstrip(".")

            typespace, type_ = qualtype.split(".") if "." in qualtype else ("", qualtype)
            type_ = camel(type_)
            qualtype = ".".join([typespace, type_]).lstrip(".")

            has_flags = bool(FLAGS_RE_3.findall(line))

            args = ARGS_RE.findall(line)

            # Fix arg names that are Python reserved keywords
            for i, item in enumerate(args):
                if item[0] in SYNTAX_RESERVED:
                    args[i] = (RESERVED_KEYWORDS[item[0]], item[1])

            combinator = Combinator(
                section=section,
                qualname=qualname,
                namespace=namespace,
                name=name,
                id=f"0x{id_hex}",
                has_flags=has_flags,
                args=args,
                qualtype=qualtype,
                typespace=typespace,
                type=type_
            )

            combinators.append(combinator)

    # Build relationship maps
    for c in combinators:
        qualtype = c.qualtype

        if qualtype.startswith("Vector"):
            qualtype = qualtype.split("<")[1][:-1]

        d = types_to_constructors if c.section == "types" else types_to_functions

        if qualtype not in d:
            d[qualtype] = []

        d[qualtype].append(c.qualname)

        if c.section == "types":
            key = c.namespace

            if key not in namespaces_to_types:
                namespaces_to_types[key] = []

            if c.type not in namespaces_to_types[key]:
                namespaces_to_types[key].append(c.type)

    for k, v in types_to_constructors.items():
        for i in v:
            try:
                constructors_to_functions[i] = types_to_functions[k]
            except KeyError:
                pass

    # --- Generate base types ---

    for qualtype in types_to_constructors:
        typespace, type_ = qualtype.split(".") if "." in qualtype else ("", qualtype)
        dir_path = DESTINATION_PATH / "base" / typespace

        module = type_
        if module == "Updates":
            module = "UpdatesT"

        os.makedirs(dir_path, exist_ok=True)

        constructors = sorted(types_to_constructors[qualtype])
        constr_count = len(constructors)
        items = "\n            ".join([f"{c}" for c in constructors])

        docstring = "Telegram API base type."
        docstring += f"\n\n    Constructors:\n" \
                     f"        This base type has {constr_count} constructor{'s' if constr_count > 1 else ''} available.\n\n" \
                     f"        .. currentmodule:: pyrogramX.raw.types\n\n" \
                     f"        .. autosummary::\n" \
                     f"            :nosignatures:\n\n" \
                     f"            {items}"

        references = types_to_functions.get(qualtype)
        if references:
            ref_count = len(references)
            ref_text = "\n            ".join(references)
            docstring += f"\n\n    Functions:\n        This object can be returned by " \
                         f"{ref_count} function{'s' if ref_count > 1 else ''}.\n\n" \
                         f"        .. currentmodule:: pyrogramX.raw.functions\n\n" \
                         f"        .. autosummary::\n" \
                         f"            :nosignatures:\n\n" \
                         f"            " + ref_text

        with open(dir_path / f"{snake(module)}.py", "w") as f:
            f.write(
                TYPE_TMPL.format(
                    notice=notice,
                    warning=WARNING,
                    docstring=docstring,
                    name=type_,
                    qualname=qualtype,
                    types=", ".join([f"raw.types.{c}" for c in constructors]),
                    doc_name=snake(type_).replace("_", "-")
                )
            )

    # --- Generate combinator classes (types + functions) ---

    for c in combinators:
        sorted_args = sort_args(c.args)

        arguments = (
            (", *, " if c.args else "") +
            (", ".join(
                [f"{i[0]}: {get_type_hint(i[1])}"
                 for i in sorted_args]
            ) if sorted_args else "")
        )

        fields = "\n        ".join(
            [f"self.{i[0]} = {i[0]}  # {i[1]}"
             for i in sorted_args]
        ) if sorted_args else "pass"

        docstring = ""
        docstring_args = []

        for i, arg in enumerate(sorted_args):
            arg_name, arg_type = arg
            is_optional = FLAGS_RE.match(arg_type)
            flag_number = is_optional.group(1) if is_optional else -1
            arg_type_clean = arg_type.split("?")[-1]

            docstring_args.append(
                "{} ({}{}):\n            N/A\n".format(
                    arg_name,
                    get_docstring_arg_type(arg_type_clean),
                    ", *optional*" if is_optional else "",
                )
            )

        if c.section == "types":
            docstring += "Telegram API type."
            docstring += f"\n\n    Constructor of :obj:`~pyrogramX.raw.base.{c.qualtype}`."
        else:
            docstring += "Telegram API function."

        docstring += f"\n\n    Details:\n        - Layer: ``{layer}``\n        - ID: ``{c.id[2:].upper()}``\n\n"
        docstring += f"    Parameters:\n        " + \
                     (f"\n        ".join(docstring_args) if docstring_args else "No parameters required.\n")

        if c.section == "functions":
            docstring += "\n    Returns:\n        " + get_docstring_arg_type(c.qualtype)
        else:
            refs = constructors_to_functions.get(c.qualname)
            if refs:
                ref_count = len(refs)
                ref_text = "\n            ".join(refs)
                docstring += f"\n    Functions:\n        This object can be returned by " \
                             f"{ref_count} function{'s' if ref_count > 1 else ''}.\n\n" \
                             f"        .. currentmodule:: pyrogramX.raw.functions\n\n" \
                             f"        .. autosummary::\n" \
                             f"            :nosignatures:\n\n" \
                             f"            " + ref_text

        # --- Build read_types and write_types ---
        write_types = read_types = "" if c.has_flags else "# No flags\n        "

        for arg_name, arg_type in c.args:
            flag = FLAGS_RE_2.match(arg_type)

            # Handle flags field
            if re.match(r"flags\d?", arg_name) and arg_type == "#":
                write_flags = []

                for i in c.args:
                    flag_match = FLAGS_RE_2.match(i[1])
                    if flag_match:
                        if arg_name != f"flags{flag_match.group(1)}":
                            continue
                        if flag_match.group(3) == "true" or flag_match.group(3).startswith("Vector"):
                            write_flags.append(f"{arg_name} |= (1 << {flag_match.group(2)}) if self.{i[0]} else 0")
                        else:
                            write_flags.append(
                                f"{arg_name} |= (1 << {flag_match.group(2)}) if self.{i[0]} is not None else 0")

                write_flags_str = "\n        ".join([
                    f"{arg_name} = 0",
                    "\n        ".join(write_flags),
                    f'b.write(pack("<I", {arg_name}))\n        '
                ])

                write_types += write_flags_str
                read_types += f'\n        {arg_name} = unpack("<i", b.read(4))[0]\n        '
                continue

            # Handle flagged (optional) fields
            if flag:
                number, index, flag_type = flag.groups()

                if flag_type == "true":
                    read_types += "\n        "
                    read_types += f"{arg_name} = True if flags{number} & (1 << {index}) else False"
                elif flag_type in CORE_TYPES:
                    write_types += "\n        "
                    write_types += f"if self.{arg_name} is not None:\n            "
                    write_types += _get_write_stmt(arg_name, flag_type) + "\n        "

                    read_types += "\n        "
                    read_types += f"{arg_name} = {_get_read_expr(flag_type)} if flags{number} & (1 << {index}) else None"
                elif "vector" in flag_type.lower():
                    sub_type = arg_type.split("<")[1][:-1]

                    write_types += "\n        "
                    write_types += f"if self.{arg_name} is not None:\n            "
                    write_types += "Vector.write_to(self.{}, b{})\n        ".format(
                        arg_name, f", {sub_type.title()}" if sub_type in CORE_TYPES else ""
                    )

                    read_types += "\n        "
                    read_types += "{} = TLObject.read(b{}) if flags{} & (1 << {}) else []\n        ".format(
                        arg_name, f", {sub_type.title()}" if sub_type in CORE_TYPES else "", number, index
                    )
                else:
                    write_types += "\n        "
                    write_types += f"if self.{arg_name} is not None:\n            "
                    write_types += f"self.{arg_name}._write_to(b)\n        "

                    read_types += "\n        "
                    read_types += f"{arg_name} = TLObject.read(b) if flags{number} & (1 << {index}) else None\n        "
            else:
                # Non-flagged (required) fields
                if arg_type in CORE_TYPES:
                    write_types += "\n        "
                    write_types += _get_write_stmt(arg_name, arg_type) + "\n        "

                    read_types += "\n        "
                    read_types += f"{arg_name} = {_get_read_expr(arg_type)}\n        "
                elif "vector" in arg_type.lower():
                    sub_type = arg_type.split("<")[1][:-1]

                    write_types += "\n        "
                    write_types += "Vector.write_to(self.{}, b{})\n        ".format(
                        arg_name, f", {sub_type.title()}" if sub_type in CORE_TYPES else ""
                    )

                    read_types += "\n        "
                    read_types += "{} = TLObject.read(b{})\n        ".format(
                        arg_name, f", {sub_type.title()}" if sub_type in CORE_TYPES else ""
                    )
                else:
                    write_types += "\n        "
                    write_types += f"self.{arg_name}._write_to(b)\n        "

                    read_types += "\n        "
                    read_types += f"{arg_name} = TLObject.read(b)\n        "

        slots = ", ".join([f'"{i[0]}"' for i in sorted_args])
        # Ensure single-element tuples have trailing comma
        if len(sorted_args) == 1:
            slots += ","
        return_arguments = ", ".join([f"{i[0]}={i[0]}" for i in sorted_args])

        compiled_combinator = COMBINATOR_TMPL.format(
            notice=notice,
            warning=WARNING,
            name=c.name,
            docstring=docstring,
            slots=slots,
            id=c.id,
            qualname=f"{c.section}.{c.qualname}",
            arguments=arguments,
            fields=fields,
            read_types=read_types,
            write_types=write_types,
            return_arguments=return_arguments
        )

        directory = "types" if c.section == "types" else c.section

        dir_path = DESTINATION_PATH / directory / c.namespace

        os.makedirs(dir_path, exist_ok=True)

        module = c.name
        if module == "Updates":
            module = "UpdatesT"

        with open(dir_path / f"{snake(module)}.py", "w") as f:
            f.write(compiled_combinator)

        d = namespaces_to_constructors if c.section == "types" else namespaces_to_functions

        if c.namespace not in d:
            d[c.namespace] = []

        d[c.namespace].append(c.name)

    # --- Generate __init__.py files ---

    for namespace, types in namespaces_to_types.items():
        with open(DESTINATION_PATH / "base" / namespace / "__init__.py", "w") as f:
            f.write(f"{notice}\n\n")
            f.write(f"{WARNING}\n\n")

            for t in types:
                module = t
                if module == "Updates":
                    module = "UpdatesT"
                f.write(f"from .{snake(module)} import {t}\n")

            if not namespace:
                f.write(f"from . import {', '.join(filter(bool, namespaces_to_types))}")

    for namespace, types in namespaces_to_constructors.items():
        with open(DESTINATION_PATH / "types" / namespace / "__init__.py", "w") as f:
            f.write(f"{notice}\n\n")
            f.write(f"{WARNING}\n\n")

            for t in types:
                module = t
                if module == "Updates":
                    module = "UpdatesT"
                f.write(f"from .{snake(module)} import {t}\n")

            if not namespace:
                f.write(f"from . import {', '.join(filter(bool, namespaces_to_constructors))}\n")

    for namespace, types in namespaces_to_functions.items():
        with open(DESTINATION_PATH / "functions" / namespace / "__init__.py", "w") as f:
            f.write(f"{notice}\n\n")
            f.write(f"{WARNING}\n\n")

            for t in types:
                module = t
                if module == "Updates":
                    module = "UpdatesT"
                f.write(f"from .{snake(module)} import {t}\n")

            if not namespace:
                f.write(f"from . import {', '.join(filter(bool, namespaces_to_functions))}")

    # --- Generate all.py ---

    with open(DESTINATION_PATH / "all.py", "w", encoding="utf-8") as f:
        f.write(notice + "\n\n")
        f.write(WARNING + "\n\n")
        f.write(f"layer = {layer}\n\n")
        f.write("objects = {")

        for c in combinators:
            f.write(f'\n    {c.id}: "pyrogramX.raw.{c.section}.{c.qualname}",')

        # Core types (hand-written)
        f.write('\n    0xbc799737: "pyrogramX.raw.core.BoolFalse",')
        f.write('\n    0x997275b5: "pyrogramX.raw.core.BoolTrue",')
        f.write('\n    0x1cb5c415: "pyrogramX.raw.core.Vector",')
        f.write('\n    0x73f1f8dc: "pyrogramX.raw.core.MsgContainer",')
        f.write('\n    0xae500895: "pyrogramX.raw.core.FutureSalts",')
        f.write('\n    0x0949d9dc: "pyrogramX.raw.core.FutureSalt",')
        f.write('\n    0x3072cfa1: "pyrogramX.raw.core.GzipPacked",')
        f.write('\n    0x5bb8e511: "pyrogramX.raw.core.Message",')

        f.write("\n}\n")

    # --- Summary ---
    type_count = sum(1 for c in combinators if c.section == "types")
    func_count = sum(1 for c in combinators if c.section == "functions")
    base_count = len(types_to_constructors)

    print(f"Compiled Layer {layer}")
    print(f"  Types:     {type_count}")
    print(f"  Functions: {func_count}")
    print(f"  Base:      {base_count}")
    print(f"  Total:     {type_count + func_count + base_count} classes")

    # Save schema hash for incremental compilation
    hash_file.parent.mkdir(parents=True, exist_ok=True)
    hash_file.write_text(current_hash)


def _get_write_stmt(arg_name: str, arg_type: str) -> str:
    """Get the optimized write statement for a core type field in _write_to."""
    pattern = WRITE_CORE.get(arg_type)
    if pattern:
        return pattern.format(name=arg_name)
    return f"b.write({arg_type.title()}(self.{arg_name}))"


def _get_read_expr(arg_type: str) -> str:
    """Get the optimized read expression for a core type field."""
    return READ_CORE.get(arg_type, f"{arg_type.title()}.read(b)")


if __name__ == "__main__":
    HOME_PATH = Path("../..")
    DESTINATION_PATH = Path("../../pyrogramX/raw")
    NOTICE_PATH = Path("../../NOTICE")
    start()
