# polyxios-data

This repository contains test data for [polyxios](https://github.com/fury-gl/polyxios).

---

## Data Disclaimer & Attribution

The assets bundled within this repository **are not our proprietary property**.

* This repository functions as a curated collection of public domain files, academic benchmark sets, and open-source assets gathered from multiple independent upstream sources. They are used **strictly for testing, parser compliance validation, and performance benchmarking**.
* All assets remain the explicit intellectual property and copyright of their respective authors, original creators, or source repositories.
* These files are redistributed under standard non-commercial research, validation, and testing provisions. If you are the author/copyright holder of any asset included here and wish to have it modified or removed, please open an issue in this repository.

---

## How to Use & Fetch Data

### 1. Programmatic Usage (Within Python via Polyxios)

The `polyxios` Python package contains a high-performance, zero-dependency fetcher module that resolves files locally, downloading their respective compressed release packs behind the scenes only when required.

#### Fetch a Single File
```python
from polyxios.fetcher import fetch

# Automatically resolves to the corresponding profile directory
# Downloads and extracts the format package on the fly if not already localized
local_path = fetch("target_file.ext")
print(f"Asset localized at: {local_path}")

```

#### Fetch All Files of a Specific Format

```python
from polyxios.fetcher import fetch_by_extension

# Downloads the entire format archive bundle if missing and registers local paths
all_paths = fetch_by_extension("ext")
print(f"Synchronized {len(all_paths)} testing targets.")

```

#### Overriding the Storage Location

By default, data is stored in your user profile path under `~/.polyxios/`. You can change this behavior globally across your environment or testing pipelines by defining the `POLYXIOS_HOME` environment variable:

```bash
export POLYXIOS_HOME="/tmp/custom_test_cache"

```

---

### 2. Manual URL Fetching (Raw Endpoint API)

If you are writing alternative testing tools, using automated tools like `curl`/`wget`, or setting up continuous integration configurations outside of Python, you can fetch assets directly using the Release binary structure.

#### Fetching Stable Compressed Extension Bundles

To download a fully flattened, production-stable zip archive matching an explicit library release version, query the distribution release endpoints:

```text
https://github.com/fury-gl/polyxios-data/releases/download/<version_tag>/<format_dir>.zip
```

*Example:*

```bash
curl https://github.com/fury-gl/polyxios-data/releases/download/v0.1.0/ply.zip

```

