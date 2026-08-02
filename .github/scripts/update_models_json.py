#!/usr/bin/env python3
import os
import json
import urllib.request
import urllib.error
import re
import argparse

EXT_TO_PACKAGE = {
    "inp": "abaqus",
    "fem": "nastran",
    "vol": "netgen",
    "f3grid": "flac3d",
    "tec": "tecplot",
    "meshb": "medit",
    "xml": "dolfin",
}

def get_file_size_str(size_bytes):
    """Convert bytes to a human-readable size string.

    Parameters
    ----------
    size_bytes : int
        The file size in bytes.

    Returns
    -------
    str
        The human-readable file size string (e.g., '100 B', '1.2 KB').
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def fetch_release_by_tag(repo, tag, token):
    """Fetch release information for a specific tag via the GitHub REST API.

    Parameters
    ----------
    repo : str
        Repository owner and name (e.g. 'fury-gl/polyxios-data').
    tag : str
        The Git tag name.
    token : str
        GitHub authentication token.

    Returns
    -------
    dict | None
        The parsed release payload JSON, or None if the release is not found.
    """
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    headers = {"User-Agent": "polyxios-updater"}
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Release tag '{tag}' not found.")
            return None
        raise e

def parse_release_assets(release):
    """Parse assets from a release payload, extracting file URLs, sizes, and SHA256 hashes.

    Parameters
    ----------
    release : dict
        The release information dictionary.

    Returns
    -------
    tuple[str, dict]
        A tuple containing the release tag name and a dictionary mapping
        asset names to their metadata.
    """
    tag = release.get("tag_name")
    assets_data = {}
    for asset in release.get("assets", []):
        name = asset.get("name")
        download_url = asset.get("browser_download_url")
        size = asset.get("size", 0)
        digest = asset.get("digest")
        if not name or not download_url or not digest or not digest.startswith("sha256:"):
            continue
        sha256_hex = digest.split(":", 1)[1]
        assets_data[name] = {
            "url": download_url,
            "sha256": sha256_hex,
            "size_bytes": size,
            "size_pretty": get_file_size_str(size)
        }
    return tag, assets_data

def main():
    """Main entry point to update the models.json catalog and README.md."""
    parser = argparse.ArgumentParser(description="Update models.json catalog.")
    parser.add_argument("--tag", help="The release tag that triggered the update (optional).")
    parser.add_argument("--action", help="The release event action (optional, e.g., 'deleted').")
    args = parser.parse_args()

    repo = os.getenv("GITHUB_REPOSITORY", "fury-gl/polyxios-data")
    token = os.getenv("GITHUB_TOKEN")
    
    models_json_path = "models.json"
    
    if os.path.exists(models_json_path):
        try:
            with open(models_json_path, "r", encoding="utf-8") as f:
                models_data = json.load(f)
                formats = models_data.get("formats", {})
        except Exception as e:
            print(f"Warning: Failed to load existing models.json: {e}")
            formats = {}
    else:
        formats = {}

    if args.tag:
        if args.tag == "latest" or re.match(r"^v\d+\.\d+", args.tag):
            print(f"Skipping update for non-format tag: {args.tag}")
            return
            
        print(f"Updating catalog for specific tag: {args.tag} (Event: {args.action})")
        if args.action == "deleted":
            if args.tag in formats:
                del formats[args.tag]
                print(f"Removed release tag: {args.tag}")
        else:
            release = fetch_release_by_tag(repo, args.tag, token)
            if release:
                tag, assets_data = parse_release_assets(release)
                formats[tag] = assets_data
                print(f"Updated release tag: {tag} with {len(assets_data)} assets.")
            elif args.tag in formats:
                # Fallback if release fetch failed but tag exists (e.g. might have been deleted)
                del formats[args.tag]
                print(f"Cleaned up missing release tag: {args.tag}")
    else:
        print("Rebuilding full catalog...")
        url = f"https://api.github.com/repos/{repo}/releases"
        headers = {"User-Agent": "polyxios-updater"}
        if token:
            headers["Authorization"] = f"token {token}"
            
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as res:
                releases = json.loads(res.read().decode())
        except Exception as e:
            print(f"Error fetching releases: {e}")
            return

        formats = {}
        for r in releases:
            tag = r.get("tag_name")
            if not tag or tag == "latest" or re.match(r"^v\d+\.\d+", tag):
                continue
            print(f"Processing release tag: {tag}")
            _, assets_data = parse_release_assets(r)
            formats[tag] = assets_data

    models_data = {
        "ext_to_package": EXT_TO_PACKAGE,
        "formats": formats
    }
    
    with open(models_json_path, "w", encoding="utf-8") as f:
        json.dump(models_data, f, indent=2, sort_keys=True)
    print("Updated models.json successfully.")

    readme_path = "README.md"
    if os.path.exists(readme_path):
        table_rows = []
        for fmt in sorted(formats.keys()):
            files_count = len(formats[fmt])
            total_size_bytes = sum(info["size_bytes"] for info in formats[fmt].values())
            size_str = get_file_size_str(total_size_bytes)
            table_rows.append(f"| `{fmt}` | {fmt.upper()} | {files_count} | {size_str} |")
        table_content = "\n".join(table_rows)

        catalog_items = []
        for fmt in sorted(formats.keys()):
            files_str = ", ".join(f"`{f}`" for f in sorted(formats[fmt].keys()))
            catalog_items.append(f"- **{fmt}**: {files_str}")
        catalog_content = "\n".join(catalog_items)

        start_marker = "<!-- UNRELEASED_RELEASE_START -->"
        release_block = f"""{start_marker}
### Latest Release

### Release Details

| Format Release | Format | Files | Size |
|----------------|--------|-------|------|
{table_content}

### Model Names Catalog
<details>
<summary><b>Show all models...</b></summary>

{catalog_content}

</details>"""

        with open(readme_path, "r", encoding="utf-8") as f:
            readme_content = f.read()

        if start_marker in readme_content:
            start_idx = readme_content.find(start_marker)
            following_text = readme_content[start_idx + len(start_marker) : start_idx + len(start_marker) + 200]
            if "### Latest Release" in following_text:
                first_details_close = readme_content.find("</details>", start_idx)
                if first_details_close != -1:
                    end_idx = first_details_close + len("</details>")
                    new_content = readme_content[:start_idx] + release_block + readme_content[end_idx:]
                else:
                    new_content = readme_content.replace(start_marker, release_block)
            else:
                new_content = readme_content[:start_idx] + release_block + readme_content[start_idx + len(start_marker) :]
        else:
            releases_header = "## Releases"
            if releases_header in readme_content:
                header_idx = readme_content.find(releases_header)
                insert_idx = readme_content.find("\n", header_idx) + 1
                new_content = readme_content[:insert_idx] + "\n" + release_block + "\n" + readme_content[insert_idx:]
            else:
                new_content = readme_content + "\n\n" + release_block

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Updated README.md successfully.")

if __name__ == "__main__":
    main()
