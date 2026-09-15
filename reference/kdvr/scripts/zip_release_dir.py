"""Zip a release directory using forward-slash entry names (itch.io-safe)."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


def zip_directory(package_dir: Path, archive_path: Path) -> int:
    """Write *archive_path* from files under *package_dir*. Returns file count."""
    if not package_dir.is_dir():
        raise FileNotFoundError(f"Package directory not found: {package_dir}")

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        archive_path.unlink()

    file_count = 0
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(package_dir.rglob("*")):
            if not path.is_file():
                continue
            # as_posix() => forward slashes; required by itch / Go zip extractors.
            arcname = path.relative_to(package_dir).as_posix()
            zf.write(path, arcname)
            file_count += 1

    with zipfile.ZipFile(archive_path, "r") as zf:
        names = zf.namelist()
        bad = [
            name
            for name in names
            if "\\" in name or name.startswith("/") or any(part == ".." for part in name.split("/"))
        ]
    if bad:
        raise SystemExit(f"Zip contains unsafe or backslash paths: {bad[:5]!r}")
    if file_count == 0:
        raise SystemExit(f"No files found under {package_dir}")
    return file_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("archive_path", type=Path)
    args = parser.parse_args()
    count = zip_directory(args.package_dir.resolve(), args.archive_path.resolve())
    print(f"Wrote {args.archive_path} ({count} files)")


if __name__ == "__main__":
    main()
