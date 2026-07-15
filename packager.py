#!/usr/bin/env python3
"""
Model packager and README documentation updater for polyxios-data.
Packages folders into ZIP archives, creates models.json, updates README.md,
calculates SHA-256 hashes, updates fetcher.py in the polyxios repo, and verifies output.

Usage:
    python3 packager.py [-r root_dir] [-m readme_path] [-f fetcher_path]
"""
import os
import sys
import json
import zipfile
import logging
import argparse
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def package_models(root_dir):
    """
    Scans the root directory, packages each valid format directory into a zip archive
    inside the 'release' directory, and writes a models.json registry index.

    Parameters
    ----------
    root_dir : str
        The absolute path to the workspace root directory containing model directories.

    Returns
    -------
    tuple
        A tuple containing:
        - release_dir (str): The absolute path to the generated release directory.
        - models_registry (dict): Dict mapping directory names to lists of packaged file paths.
    """
    logger.info("Starting packaging process...")
    release_dir = os.path.join(root_dir, "release")
    os.makedirs(release_dir, exist_ok=True)

    dirs_to_zip = []
    skipped_dirs = {".git", "release"}

    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        if os.path.isdir(item_path):
            if item in skipped_dirs or item.startswith(".") or "release" in item_path:
                logger.info(f"Skipping folder: {item}")
                continue
            dirs_to_zip.append((item, item_path))

    models_registry = {}

    for folder_name, folder_path in sorted(dirs_to_zip):
        zip_filename = f"{folder_name}.zip"
        zip_filepath = os.path.join(release_dir, zip_filename)

        logger.info(f"Packaging {folder_name} -> {zip_filepath}")

        files_in_folder = []

        with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                dirs.sort()
                for file_item in sorted(files):
                    if file_item.startswith("."):
                        continue
                    file_path = os.path.join(root, file_item)
                    rel_path = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, rel_path)
                    if "/" not in rel_path and "\\" not in rel_path:
                        files_in_folder.append(rel_path)

        if files_in_folder:
            models_registry[folder_name] = files_in_folder

    models_json_path = os.path.join(release_dir, "models.json")
    logger.info(f"Writing registry to {models_json_path}")
    with open(models_json_path, "w", encoding="utf-8") as f:
        json.dump(models_registry, f, indent=2, sort_keys=True)

    logger.info("Packaging complete!")
    return release_dir, models_registry


def get_file_size_str(filepath):
    """
    Calculates the size of a file and returns it as a formatted human-readable string.

    Parameters
    ----------
    filepath : str
        The path to the file.

    Returns
    -------
    str
        Formatted file size (e.g. '1.2 MB', '4.4 KB', '999 B'). Returns 'TBD' on failure.
    """
    try:
        size_bytes = os.path.getsize(filepath)
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    except Exception as e:
        logger.warning(f"Failed to get file size for {filepath}: {e}")
        return "TBD"


def update_readme(readme_path, root_dir, registry):
    """
    Updates the README.md file in-place, adding/replacing the unreleased details block
    under the start marker with the current packaged format table and model lists.

    Parameters
    ----------
    readme_path : str
        The absolute path to the README.md file.
    root_dir : str
        The root directory containing format folders.
    registry : dict
        Dict mapping format folders to lists of file paths.

    Returns
    -------
    None
    """
    if not os.path.exists(readme_path):
        logger.warning(f"README.md not found at {readme_path}, skipping update.")
        return

    table_rows = []
    for k in sorted(registry.keys()):
        fmt_name = k.upper()
        files_count = len(registry[k])
        zip_filepath = os.path.join(root_dir, "release", f"{k}.zip")
        size_str = get_file_size_str(zip_filepath)
        table_rows.append(f"| `{k}.zip` | {fmt_name} | {files_count} | {size_str} |")
    table_content = "\n".join(table_rows)

    catalog_items = []
    total_files = 0
    for k in sorted(registry.keys()):
        files_str = ", ".join(f"`{f}`" for f in registry[k])
        catalog_items.append(f"- **{k}**: {files_str}")
        total_files += len(registry[k])
    catalog_content = "\n".join(catalog_items)

    start_marker = "<!-- UNRELEASED_RELEASE_START -->"

    release_block = f"""{start_marker}
### Latest Release

### Release Details

| Archive | Format | Files | Size |
|---------|--------|-------|------|
{table_content}

### Model Names Catalog
<details>
<summary><b>Show all models...</b></summary>

{catalog_content}

</details>"""

    with open(readme_path, "r", encoding="utf-8") as f:
        readme_content = f.read()

    if start_marker in readme_content:
        logger.info("Found unreleased release start marker in README.md. Updating in-place...")
        start_idx = readme_content.find(start_marker)

        # Check if the unreleased details placeholder exists after the start marker (within 200 chars)
        following_text = readme_content[
            start_idx + len(start_marker) : start_idx + len(start_marker) + 200
        ]
        if "### Latest Release" in following_text:
            first_details_close = readme_content.find("</details>", start_idx)
            if first_details_close != -1:
                end_idx = first_details_close + len("</details>")
                new_content = (
                    readme_content[:start_idx]
                    + release_block
                    + readme_content[end_idx:]
                )
            else:
                new_content = readme_content.replace(start_marker, release_block)
        else:
            new_content = (
                readme_content[:start_idx]
                + release_block
                + readme_content[start_idx + len(start_marker) :]
            )
    else:
        logger.info("Marker not found in README.md. Inserting under ## Releases...")
        releases_header = "## Releases"
        if releases_header in readme_content:
            header_idx = readme_content.find(releases_header)
            insert_idx = readme_content.find("\n", header_idx) + 1
            new_content = (
                readme_content[:insert_idx]
                + "\n"
                + release_block
                + "\n"
                + readme_content[insert_idx:]
            )
        else:
            logger.warning("Could not find ## Releases header. Appending to end.")
            new_content = readme_content + "\n\n" + release_block

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    logger.info("README.md updated successfully.")


def calculate_sha256(filepath):
    """
    Computes the SHA-256 hash of a file.

    Parameters
    ----------
    filepath : str
        The path to the file.

    Returns
    -------
    str
        The SHA-256 hex string.
    """
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def update_fetcher(fetcher_path, release_dir, registry):
    """
    Updates the _PACKAGES dict inside fetcher.py with the computed SHA-256 hashes
    of the newly generated zip files.

    Parameters
    ----------
    fetcher_path : str
        Path to fetcher.py.
    release_dir : str
        Path to the release directory containing the zips.
    registry : dict
        Dict mapping format folders to expected lists of file paths.

    Returns
    -------
    None
    """
    if not fetcher_path or not os.path.exists(fetcher_path):
        logger.warning(f"Fetcher file not found at {fetcher_path}, skipping fetcher SHA update.")
        return

    # Calculate SHA256 for each generated zip
    pkg_shas = {}
    for k in registry.keys():
        zip_path = os.path.join(release_dir, f"{k}.zip")
        if os.path.exists(zip_path):
            pkg_shas[k] = calculate_sha256(zip_path)

    with open(fetcher_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the _PACKAGES dict start and end
    start_marker = "_PACKAGES: dict[str, str] = {"
    start_idx = content.find(start_marker)
    if start_idx == -1:
        logger.warning("Could not find _PACKAGES dictionary in fetcher.py")
        return

    end_idx = content.find("}", start_idx)
    if end_idx == -1:
        logger.warning("Could not find end of _PACKAGES dictionary in fetcher.py")
        return

    # Parse existing packages dict and update it
    dict_content = content[start_idx + len(start_marker):end_idx]
    
    lines = dict_content.splitlines()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            new_lines.append(line)
            continue
        if ":" in stripped:
            parts = stripped.split(":", 1)
            key = parts[0].strip().strip('"').strip("'")
            if key in pkg_shas:
                indent = line[:line.find(parts[0])]
                new_lines.append(f'{indent}"{key}": "{pkg_shas[key]}",')
                continue
        new_lines.append(line)

    new_dict_content = "\n".join(new_lines)
    new_content = content[:start_idx + len(start_marker)] + new_dict_content + content[end_idx:]

    with open(fetcher_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    logger.info(f"Successfully updated fetcher.py _PACKAGES SHA-256 hashes.")


def run_tests(root_dir, release_dir, original_registry):
    """
    Runs verification and integrity tests on the packaged release files.

    Parameters
    ----------
    root_dir : str
        The workspace root directory.
    release_dir : str
        The generated release directory containing zips and models.json.
    original_registry : dict
        Dict mapping format folders to expected lists of file paths.

    Raises
    ------
    AssertionError
        If any of the integrity or checklist validation tests fail.
    """
    logger.info("Running verification tests...")

    assert os.path.exists(release_dir), "Release directory does not exist!"

    models_json_path = os.path.join(release_dir, "models.json")
    assert os.path.exists(models_json_path), "models.json does not exist!"

    with open(models_json_path, "r", encoding="utf-8") as f:
        loaded_registry = json.load(f)

    assert loaded_registry == original_registry, (
        "Loaded models.json doesn't match original registry!"
    )
    logger.info("models.json validation: PASSED")

    for folder_name, expected_files in original_registry.items():
        zip_filename = f"{folder_name}.zip"
        zip_filepath = os.path.join(release_dir, zip_filename)

        assert os.path.exists(zip_filepath), (
            f"Expected zip file {zip_filepath} does not exist!"
        )

        with zipfile.ZipFile(zip_filepath, "r") as zipf:
            test_result = zipf.testzip()
            assert test_result is None, (
                f"Zip file {zip_filename} is corrupted: {test_result}"
            )

            members = zipf.namelist()
            top_level_members = [m for m in members if "/" not in m and "\\" not in m]
            assert sorted(top_level_members) == sorted(expected_files), (
                f"Zip file {zip_filename} file list mismatch! Expected {expected_files}, got {top_level_members}"
            )

        logger.info(f"ZIP {zip_filename} validation (integrity & file checklist): PASSED")

    logger.info("All tests passed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Package polyxios-data model folders into release zip archives, update README, and update fetcher SHAs."
    )
    parser.add_argument("-r", "--root-dir", help="Root directory containing model format segregated into folders.")
    parser.add_argument("-m", "--readme", help="Path to README.md to be updated in-place.")
    parser.add_argument("-f", "--fetcher", help="Path to fetcher.py to update SHA-256 hashes.")

    args = parser.parse_args()

    root_dir = args.root_dir
    if not root_dir:
        while True:
            val = input("Enter the models root directory path: ").strip()
            if val:
                root_dir = os.path.abspath(val)
                if os.path.exists(root_dir) and os.path.isdir(root_dir):
                    break
                else:
                    print(f"Directory '{val}' does not exist. Please enter a valid directory.")
            else:
                print("Directory path cannot be empty.")
    else:
        root_dir = os.path.abspath(root_dir)
        if not os.path.exists(root_dir) or not os.path.isdir(root_dir):
            logger.error(f"Provided root directory '{root_dir}' does not exist or is not a directory.")
            sys.exit(1)

    readme_path = args.readme
    if not readme_path:
        while True:
            val = input("Enter the README.md path: ").strip()
            if val:
                readme_path = os.path.abspath(val)
                if os.path.exists(readme_path) and os.path.isfile(readme_path):
                    break
                else:
                    print(f"File '{val}' does not exist. Please enter a valid file path.")
            else:
                print("README.md path cannot be empty.")
    else:
        readme_path = os.path.abspath(readme_path)
        if not os.path.exists(readme_path) or not os.path.isfile(readme_path):
            logger.error(f"Provided README path '{readme_path}' does not exist or is not a file.")
            sys.exit(1)

    fetcher_path = args.fetcher
    if not fetcher_path:
        while True:
            val = input("Enter the fetcher.py path: ").strip()
            if val:
                fetcher_path = os.path.abspath(val)
                if os.path.exists(fetcher_path) and os.path.isfile(fetcher_path):
                    break
                else:
                    print(f"File '{val}' does not exist. Please enter a valid file path.")
            else:
                print("fetcher.py path cannot be empty.")
    else:
        fetcher_path = os.path.abspath(fetcher_path)
        if not os.path.exists(fetcher_path) or not os.path.isfile(fetcher_path):
            logger.error(f"Provided fetcher path '{fetcher_path}' does not exist or is not a file.")
            sys.exit(1)

    logger.info(f"Using root directory: {root_dir}")
    logger.info(f"Using README path: {readme_path}")
    logger.info(f"Using fetcher path: {fetcher_path}")

    release_dir, registry = package_models(root_dir)
    run_tests(root_dir, release_dir, registry)
    update_readme(readme_path, root_dir, registry)
    update_fetcher(fetcher_path, release_dir, registry)
