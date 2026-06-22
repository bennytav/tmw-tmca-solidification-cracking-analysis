"""Install local raw data into the repository `raw_data/` folder.

This helper is for the small code-only package.  The manuscript manifests expect
raw controller logs at paths such as:

    raw_data/TMCA/<campaign>/<run>.xml
    raw_data/TMW/<campaign>/<run>.xml

If you already have `raw_private.zip` or an extracted `raw_private/` folder, use
this script instead of manually moving folders.

Examples
--------
Install from a zip file:

    python scripts/11_install_local_raw_data.py --zip "D:/path/raw_private.zip"

Install from an extracted folder:

    python scripts/11_install_local_raw_data.py --folder "D:/path/raw_private"

Overwrite existing raw_data/TMCA and raw_data/TMW:

    python scripts/11_install_local_raw_data.py --zip "D:/path/raw_private.zip" --overwrite
"""
from __future__ import annotations

import argparse
import shutil
import tempfile
import zipfile
from pathlib import Path

from _bootstrap import bootstrap
ROOT = bootstrap(__file__)


def _find_protocol_folders(base: Path) -> tuple[Path, Path]:
    """Return paths to TMCA and TMW folders inside an extracted raw-data tree.

    The uploaded raw archive may have either of these layouts:

        raw_private/TMCA/...
        raw_private/TMW/...

    or:

        TMCA/...
        TMW/...

    This function searches for the first matching pair and raises a clear error
    if it cannot find both folders.
    """
    candidates = [base, base / "raw_private"]
    candidates += [p for p in base.iterdir() if p.is_dir()]

    for candidate in candidates:
        tmca = candidate / "TMCA"
        tmw = candidate / "TMW"
        if tmca.exists() and tmw.exists():
            return tmca, tmw

    raise FileNotFoundError(
        "Could not find both TMCA/ and TMW/ folders. Expected either "
        "raw_private/TMCA + raw_private/TMW or TMCA + TMW."
    )


def _copy_protocol_folder(src: Path, dst: Path, *, overwrite: bool) -> None:
    """Copy one protocol folder into raw_data/.

    Existing folders are protected by default to prevent accidental deletion of
    local data.  Use --overwrite only if you intentionally want to replace them.
    """
    if dst.exists() and any(dst.iterdir()) and not overwrite:
        raise FileExistsError(
            f"Destination already contains files: {dst}\n"
            "Use --overwrite to replace it, or delete the folder manually."
        )
    if dst.exists() and overwrite:
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)


def _count_files(folder: Path) -> tuple[int, int]:
    """Return number of XML files and total files under a folder."""
    xml_count = sum(1 for p in folder.rglob("*.xml") if p.is_file())
    total_count = sum(1 for p in folder.rglob("*") if p.is_file())
    return xml_count, total_count


def install_from_folder(folder: Path, *, overwrite: bool) -> None:
    """Install raw data from an already extracted folder."""
    tmca_src, tmw_src = _find_protocol_folders(folder)
    tmca_dst = ROOT / "raw_data" / "TMCA"
    tmw_dst = ROOT / "raw_data" / "TMW"

    print(f"TMCA source: {tmca_src}")
    print(f"TMW  source: {tmw_src}")
    _copy_protocol_folder(tmca_src, tmca_dst, overwrite=overwrite)
    _copy_protocol_folder(tmw_src, tmw_dst, overwrite=overwrite)

    tmca_xml, tmca_total = _count_files(tmca_dst)
    tmw_xml, tmw_total = _count_files(tmw_dst)
    print("\nRaw data installed successfully.")
    print(f"TMCA: {tmca_xml} XML files, {tmca_total} total files -> {tmca_dst.relative_to(ROOT)}")
    print(f"TMW : {tmw_xml} XML files, {tmw_total} total files -> {tmw_dst.relative_to(ROOT)}")


def install_from_zip(zip_path: Path, *, overwrite: bool) -> None:
    """Extract a raw-data zip to a temporary folder and install TMCA/TMW folders."""
    if not zip_path.exists():
        raise FileNotFoundError(zip_path)
    with tempfile.TemporaryDirectory(prefix="tmw_tmca_raw_extract_") as tmp:
        tmp_path = Path(tmp)
        print(f"Extracting {zip_path} ...")
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp_path)
        install_from_folder(tmp_path, overwrite=overwrite)


def main() -> None:
    parser = argparse.ArgumentParser(description="Install local raw TMCA/TMW data into raw_data/.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--zip", type=Path, help="Path to raw_private.zip or similar raw-data zip.")
    src.add_argument("--folder", type=Path, help="Path to extracted raw_private folder or a folder containing TMCA/ and TMW/.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing raw_data/TMCA and raw_data/TMW folders.")
    args = parser.parse_args()

    if args.zip:
        install_from_zip(args.zip, overwrite=args.overwrite)
    else:
        install_from_folder(args.folder, overwrite=args.overwrite)

    print("\nNext quick check:")
    print("  python scripts/10_run_benny_raw_data_workflow.py --limit-per-protocol 2")
    print("Then full run:")
    print("  python scripts/10_run_benny_raw_data_workflow.py")


if __name__ == "__main__":
    main()
