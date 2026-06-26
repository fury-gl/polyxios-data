# polyxios-data

Test data for [polyxios](https://github.com/fury-gl/polyxios) codec integration testing.
Assets are downloaded on demand via `polyxios.fetcher` — nothing is bundled in the package itself.

---

## Releases

### v0.2.0 — small curated codec test files (18 formats)

| Archive | Format | Files | License |
|---------|--------|-------|---------|
| `abaqus.zip` | Abaqus `.inp` | 5 | MIT / GPL-2.0 |
| `avs.zip` | AVS/UCD `.avs` | 1 | BSD |
| `dolfin.zip` | DOLFIN XML `.xml` | 1 | LGPL-3.0 |
| `flac3d.zip` | FLAC3D `.f3grid` | 1 | MIT |
| `gmsh.zip` | Gmsh `.msh` v2.2 + v4.1 | 2 | MIT |
| `mdpa.zip` | Kratos `.mdpa` | 2 | BSD (4-clause) |
| `medit.zip` | Medit `.mesh` + `.meshb` | 6 | MIT / LGPL-3.0 |
| `nastran.zip` | Nastran BDF `.fem` | 2 | MIT |
| `netgen.zip` | Netgen `.vol` | 3 | MIT |
| `obj.zip` | Wavefront OBJ `.obj` | 1 | MIT |
| `off.zip` | OFF `.off` | 4 | MIT / MPL-2.0 |
| `ply.zip` | Stanford PLY `.ply` | 2 | MIT / Stanford |
| `stl.zip` | STL `.stl` | 2 | MIT |
| `su2.zip` | SU2 `.su2` | 2 | MIT |
| `tecplot.zip` | Tecplot ASCII `.tec` | 3 | MIT |
| `tetgen.zip` | TetGen `.ele`+`.node` | 1 mesh | MIT |
| `ugrid.zip` | AFLR UGRID `.ugrid` | 1 | MIT |
| `wkt.zip` | WKT `.wkt` | 2 | MIT |

Each archive contains a `README.md` with per-file source and license details.

### v0.1.0 — large curated mesh collections (8 formats)

| Archive | Format | Size |
|---------|--------|------|
| `mesh.zip` | Medit mesh | 135 KB |
| `msh.zip` | Gmsh MSH | 218 KB |
| `obj.zip` | Wavefront OBJ | 30 MB |
| `ply.zip` | Stanford PLY | 78 MB |
| `vtk.zip` | VTK Legacy | 11 MB |
| `vtp.zip` | VTK PolyData | 1.2 MB |
| `vtr.zip` | VTK RectilinearGrid | 1.5 MB |
| `vtu.zip` | VTK UnstructuredGrid | 6 KB |

---

## Attribution & Disclaimer

Assets are curated from public-domain files, academic benchmark sets, and open-source
repositories. They are used **strictly for testing, parser compliance validation, and
performance benchmarking**. All files remain the intellectual property of their respective
authors. If you are the copyright holder of any asset and wish it removed, please open an issue.

Sources used in v0.2.0:

| Repository | License |
|-----------|---------|
| [nschloe/meshio](https://github.com/nschloe/meshio) | MIT |
| [mikedh/trimesh](https://github.com/mikedh/trimesh) | MIT |
| [MmgTools/Mmg](https://github.com/MmgTools/Mmg) | LGPL-3.0 |
| [RBniCS/RBniCS](https://github.com/RBniCS/RBniCS) | LGPL-3.0 |
| [libigl/libigl-tutorial-data](https://github.com/libigl/libigl-tutorial-data) | MPL-2.0 |
| [KratosMultiphysics/Kratos](https://github.com/KratosMultiphysics/Kratos) | BSD (4-clause) |
| [lanl/LaGriT](https://github.com/lanl/LaGriT) | BSD (LA-CC-15-069) |
| [calculix/ccx_prool](https://github.com/calculix/ccx_prool) | GPL-2.0 |

`ply/bun_zipper_res4.ply` — Stanford 3D Scanning Repository.
Free for any use with acknowledgment: http://graphics.stanford.edu/data/3Dscanrep/

---

## Usage

### Fetch via polyxios (recommended)

```python
from polyxios.fetcher import fetch, fetch_by_extension

# Fetch a single file — downloads the format archive on first use
path = fetch("cube86.mesh")         # medit format
path = fetch("pyra_cube.ugrid")     # ugrid format
path = fetch("20mm-xyz-cube.stl")   # stl format

# Fetch all files of a format
paths = fetch_by_extension(".inp")  # all abaqus test files
```

Data is cached in `~/.polyxios/` (override with `POLYXIOS_HOME` env var).

### Direct download via curl / wget

```bash
# Format: https://github.com/fury-gl/polyxios-data/releases/download/<tag>/<format>.zip

curl -LO https://github.com/fury-gl/polyxios-data/releases/download/v0.2.0/medit.zip
curl -LO https://github.com/fury-gl/polyxios-data/releases/download/v0.1.0/ply.zip
```
