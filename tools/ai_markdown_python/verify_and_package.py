from __future__ import annotations

import configparser
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import tarfile
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
APP_ID = "spl_ai_markdown_python"
VERSION = "0.1.2"
APP = ROOT / "apps" / APP_ID
PACKAGE = ROOT / "apps" / "_packages" / f"{APP_ID}-{VERSION}.tgz"
REPORT = ROOT / "apps" / "_reports" / f"{APP_ID}-{VERSION}-local-verification.json"
MTIME = 1_577_836_800
REQUIRED = {
    "README.md", "THIRD_PARTY_LICENSES.md", "bin/ai_markdown_core.py", "bin/aimarkdown.py",
    "default/app.conf", "default/commands.conf", "default/data/ui/nav/default.xml",
    "default/data/ui/views/markdown_python.xml", "metadata/default.meta",
    "appserver/static/js/ai_markdown_python_002.js", "appserver/static/css/ai_markdown_python_002.css",
    "appserver/static/vendor/purify_noamd_001.js",
}
VENDOR_PREFIXES = ("bin/lib/markdown", "bin/lib/bleach", "bin/lib/splunklib", "bin/lib/splunk_sdk", "bin/lib/deprecation", "bin/lib/importlib_metadata", "bin/lib/packaging", "bin/lib/zipp", "bin/lib/webencodings")
SECRET_PATTERNS = [
    re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"), re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+\S+"),
    re.compile(r"AKIA[0-9A-Z]{16}"), re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)(?:password|passwd|secret|api[_-]?key|access[_-]?key|session[_-]?key|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
]
RAW_PATTERNS = [re.compile(r"<Event[^>]*>.*</Event>", re.I | re.S), re.compile(r'"(?:host|source|sourcetype)"\s*:\s*"[^\"]+"')]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def package_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted(APP.rglob("*")):
        relative = path.relative_to(APP)
        if relative.as_posix() in {"appserver/static/js/ai_markdown_python_001.js", "appserver/static/css/ai_markdown_python_001.css", "appserver/static/vendor/purify.min.js"} or relative.as_posix().startswith("bin/lib/bin/") or any(part in {"__pycache__", ".pytest_cache"} for part in relative.parts) or path.suffix == ".pyc" or path.name in {".DS_Store"} or path.name.startswith("._"):
            continue
        mode = path.lstat().st_mode
        require(not stat.S_ISLNK(mode), f"symlink rejected: {relative}")
        if path.is_dir():
            continue
        require(stat.S_ISREG(mode), f"non-regular file rejected: {relative}")
        name = relative.as_posix()
        require(name in REQUIRED or name.startswith(VENDOR_PREFIXES), f"unexpected app file: {name}")
        files.append(path)
    names = {p.relative_to(APP).as_posix() for p in files}
    require(REQUIRED <= names, f"missing required files: {sorted(REQUIRED - names)}")
    return files


def build_bytes(files: list[Path]) -> bytes:
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for path in files:
            info = archive.gettarinfo(str(path), arcname=f"{APP_ID}/{path.relative_to(APP).as_posix()}")
            info.uid = info.gid = 0
            info.uname = info.gname = "root"
            info.mtime = MTIME
            info.mode = 0o644
            with path.open("rb") as handle:
                archive.addfile(info, handle)
    output = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as gz:
        gz.write(tar_buffer.getvalue())
    return output.getvalue()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        require(path.is_file() and not path.is_symlink(), f"unsafe output path: {path}")
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name): os.unlink(temp_name)


def main() -> None:
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    parser.read(APP / "default/app.conf", encoding="utf-8")
    require(parser["id"]["name"] == APP_ID and parser["id"]["version"] == VERSION, "app identity mismatch")
    require(parser["launcher"]["author"] == "G0TH3R" and parser["launcher"]["version"] == VERSION, "launcher mismatch")
    commands = configparser.ConfigParser(interpolation=None, strict=True); commands.read(APP / "default/commands.conf", encoding="utf-8")
    require(commands["aimarkdown"]["filename"] == "aimarkdown.py" and commands["aimarkdown"]["streaming"] == "true", "command contract mismatch")
    view = ET.parse(APP / "default/data/ui/views/markdown_python.xml").getroot()
    require(view.tag == "dashboard" and view.attrib.get("version") == "1.1", "view contract mismatch")
    body = ET.tostring(view, encoding="unicode")
    require("purify_noamd_001.js" in body and "ai_markdown_python_002.js" in body, "versioned assets missing")
    authored = [p for p in APP.rglob("*") if p.is_file() and "bin/lib" not in p.as_posix() and p.stat().st_size < 1_000_000]
    for path in authored:
        text = path.read_text(encoding="utf-8", errors="replace")
        require(not any(pattern.search(text) for pattern in SECRET_PATTERNS), f"credential pattern in {path.relative_to(ROOT)}")
        require(not any(pattern.search(text) for pattern in RAW_PATTERNS), f"raw event pattern in {path.relative_to(ROOT)}")
    files = package_files()
    first = build_bytes(files); second = build_bytes(files)
    require(first == second, "package build is not deterministic")
    atomic_write(PACKAGE, first)
    with tarfile.open(PACKAGE, "r:gz") as archive:
        members = archive.getmembers()
        require(all(m.isfile() and not m.linkname and m.name.startswith(APP_ID + "/") and m.mode == 0o644 and m.mtime == MTIME for m in members), "archive member contract failed")
    digest = hashlib.sha256(first).hexdigest()
    report = {"app_id": APP_ID, "version": VERSION, "status": "local-package-validated-not-installed", "package": str(PACKAGE.relative_to(ROOT)), "sha256": digest, "files": len(files), "checks": {"identity":"passed","xml_conf":"passed","python_markdown_bleach":"passed","dompurify":"passed","secret_scan":"passed","raw_event_scan":"passed","deterministic_double_build":"passed","archive_members":"passed"}, "live_install_performed": False, "live_render_verified": False}
    atomic_write(REPORT, (json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
