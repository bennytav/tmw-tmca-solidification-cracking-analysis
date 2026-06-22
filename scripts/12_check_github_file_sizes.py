"""Check whether files are safe for a normal GitHub repository.

GitHub blocks regular Git files larger than 100 MiB and warns for files larger
than 50 MiB. Run this script before pushing a repository that contains raw data.
"""
from __future__ import annotations

from pathlib import Path

WARN_MIB = 50
BLOCK_MIB = 100
WARN_BYTES = WARN_MIB * 1024 * 1024
BLOCK_BYTES = BLOCK_MIB * 1024 * 1024


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    ignored_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "outputs"}

    warn = []
    block = []
    total_bytes = 0
    file_count = 0

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored_dirs for part in path.parts):
            continue
        size = path.stat().st_size
        total_bytes += size
        file_count += 1
        if size >= BLOCK_BYTES:
            block.append((path, size))
        elif size >= WARN_BYTES:
            warn.append((path, size))

    print(f"Checked {file_count} files.")
    print(f"Total tracked-size estimate: {total_bytes / (1024**3):.2f} GiB")

    if warn:
        print(f"\nFiles above GitHub warning threshold ({WARN_MIB} MiB):")
        for path, size in warn:
            print(f"  {size / (1024**2):8.1f} MiB  {path.relative_to(root)}")
    else:
        print(f"\nNo files above {WARN_MIB} MiB.")

    if block:
        print(f"\nERROR: files above GitHub hard limit ({BLOCK_MIB} MiB):")
        for path, size in block:
            print(f"  {size / (1024**2):8.1f} MiB  {path.relative_to(root)}")
        raise SystemExit(1)

    print(f"\nNo files above GitHub hard limit ({BLOCK_MIB} MiB).")


if __name__ == "__main__":
    main()
