import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List
import argparse

import requests


HOME_PATH = Path("compiler/errors")
URLS_FILE = HOME_PATH / "data_urls.txt"
SOURCE_DIR = HOME_PATH / "source"
API_SOURCE_DIR = Path("compiler/api")

METHOD_CATEGORIES = ["bot_only", "user_only", "business_supported", "unauthed_allowed"]


def default_code_mapping() -> Dict[str, str]:
    return {
        "303": "303_SEE_OTHER.tsv",
        "400": "400_BAD_REQUEST.tsv",
        "401": "401_UNAUTHORIZED.tsv",
        "403": "403_FORBIDDEN.tsv",
        "404": "404_NOT_FOUND.tsv",
        "406": "406_NOT_ACCEPTABLE.tsv",
        "420": "420_FLOOD.tsv",
        "500": "500_INTERNAL_SERVER_ERROR.tsv",
        "503": "503_SERVICE_UNAVAILABLE.tsv",
    }


def load_urls() -> List[str]:
    if not URLS_FILE.exists():
        raise FileNotFoundError(f"Missing {URLS_FILE}")
    with open(URLS_FILE, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]


def fetch_json(url: str) -> dict:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    text = r.text.strip()
    if not text.endswith("}"):
        last = text.rfind("}")
        if last != -1:
            text = text[: last + 1]
    return json.loads(text)


def sanitize_code_name(http_code: str) -> str:
    existing = {p.name for p in SOURCE_DIR.glob("*.tsv")}
    unsigned = re.sub(r"^-", "", str(http_code))
    for name in existing:
        if name.startswith(f"{unsigned}_"):
            return name
    mapping = default_code_mapping()
    return mapping.get(unsigned, f"{unsigned}_UNKNOWN.tsv")


def read_existing(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not path.exists():
        return data
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.rstrip("\n")
            if i == 0 and line.startswith("id\t"):
                continue
            if not line:
                continue
            try:
                k, v = line.split("\t", 1)
            except ValueError:
                continue
            if k and v:
                data[k] = v
    return data


def write_tsv(path: Path, rows: Dict[str, str]) -> None:
    keys = sorted(rows.keys())
    with open(path, "w", encoding="utf-8") as f:
        f.write("id\tmessage\n")
        for i, k in enumerate(keys, start=1):
            f.write(f"{k}\t{rows[k]}")
            if i != len(keys):
                f.write("\n")


def merge_descriptions(status_block: dict, descriptions: dict, skip_empty: bool) -> Dict[str, Dict[str, str]]:
    per_code: Dict[str, Dict[str, str]] = defaultdict(dict)

    for code, err_to_methods in status_block.items():
        code_str = str(code)
        filename = sanitize_code_name(code_str)
        for error_id in err_to_methods.keys():
            normalized_id = error_id.replace('%d', 'X')
            msg = descriptions.get(error_id, "")
            msg = re.sub(r"\s+", " ", msg).strip()
            if msg:
                msg = msg.replace('%d', '{value}')
            if skip_empty and not msg:
                continue
            if not msg:
                msg = ""
            per_code[filename][normalized_id] = msg

    return per_code


def main() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    removed = 0
    for p in SOURCE_DIR.glob("*.tsv"):
        try:
            p.unlink()
            removed += 1
        except Exception:
            pass
    if removed:
        print(f"[OK] Cleared {removed} file(s) in source/")

    parser = argparse.ArgumentParser(description="Fetch error JSONs and write TSVs")
    parser.add_argument("--skip-empty", action="store_true", help="skip errors without descriptions")
    args = parser.parse_args()

    urls = load_urls()

    for filename in sorted(default_code_mapping().values()):
        path = SOURCE_DIR / filename
        if not path.exists():
            write_tsv(path, {})

    aggregated: Dict[str, Dict[str, str]] = defaultdict(dict)
    method_cats: Dict[str, set] = {cat: set() for cat in METHOD_CATEGORIES}

    for url in urls:
        try:
            data = fetch_json(url)
        except Exception as e:
            print(f"[WARN] Failed to fetch {url}: {e}")
            continue

        statuses = data.get("statuses") or data.get("errors") or {}
        descriptions = data.get("descriptions") or {}

        per_code = merge_descriptions(statuses, descriptions, skip_empty=args.skip_empty)

        for filename, rows in per_code.items():
            for k, v in rows.items():
                old = aggregated[filename].get(k)
                if not old or (not old.strip() and v.strip()):
                    aggregated[filename][k] = v
                else:
                    aggregated[filename].setdefault(k, v)

        for cat in METHOD_CATEGORIES:
            items = data.get(cat)
            if isinstance(items, list):
                method_cats[cat].update(items)

    for filename, rows in aggregated.items():
        path = SOURCE_DIR / filename
        existing = read_existing(path)
        merged = dict(existing)
        for k, v in rows.items():
            if k in merged and merged[k].strip():
                if v.strip() and merged[k].strip() != v.strip():
                    merged[k] = v
            else:
                merged[k] = v

        write_tsv(path, merged)
        print(f"[OK] Wrote {path} with {len(merged)} rows")

    API_SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    for cat in METHOD_CATEGORIES:
        items = sorted(method_cats[cat])
        if not items:
            continue
        path = API_SOURCE_DIR / f"{cat}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"[OK] Wrote {path} with {len(items)} methods")


if __name__ == "__main__":
    main()
