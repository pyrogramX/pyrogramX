import os
import requests
from typing import List, Tuple


def generate_urls(
    targets: str | list[str] = ["data/web/corefork.telegram.org/file","data/web/core.telegram.org/file"],
    repo: str = "MarshalX/telegram-crawler",
    branch: str = "data",
    token: str | None = None,
    print_output: bool = True,
    save_file: str = "compiler/errors/data_urls.txt"
) -> List[Tuple[str, str]]:
    """
    Traverse a GitHub repo folder and return a list of (sha256_path, https_url).
    """
    if isinstance(targets, str):
        targets = [targets]

    token = token or os.environ.get("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}

    def _ls(path=""):
        url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def _list_files_recursive(path: str):
        items = _ls(path)
        if not items:
            return []
        stack = [it["path"] for it in items if it["type"] == "dir"]
        files = [it["path"] for it in items if it["type"] == "file"]
        while stack:
            d = stack.pop()
            sub = _ls(d)
            if not sub:
                continue
            for it in sub:
                if it["type"] == "file":
                    files.append(it["path"])
                elif it["type"] == "dir":
                    stack.append(it["path"])
        return files

    def _to_https_url(path: str) -> str:
        if path.endswith(".sha256"):
            path = path[:-len(".sha256")]
        if path.startswith("data/web/"):
            path = path[len("data/web/"):]
        return f"https://{path}"

    results: List[Tuple[str, str]] = []
    all_urls: List[str] = []

    for target in targets:
        files = _list_files_recursive(target)
        if not files:
            continue
        for f in files:
            url = _to_https_url(f)
            results.append((f, url))
            all_urls.append(url)
            if print_output:
                print(url)

    if all_urls:
        with open(save_file, "w", encoding="utf-8") as f_out:
            f_out.write("\n".join(all_urls))
        print(f"[DONE] Saved {len(all_urls)} URLs to {save_file}")
    else:
        print("[WARN] No URLs found.")

    return results

if __name__ == "__main__":
    generate_urls()
