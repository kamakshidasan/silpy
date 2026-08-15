# silpy

silpy is a Python research library for topological analysis and simplification of scalar fields on triangulated surface meshes. It builds critical-point representations, join and split merge trees, branch decompositions, branch hierarchies, segmentations, and bottleneck distances on top of PyVista and NetworkX.

The repository currently provides a source package rather than an installable Python distribution or command-line application.

## Features

- Build a triangulated PyVista field from a 2D NumPy array or a random mixture of Gaussians.
- Classify mesh vertices as minima, maxima, regular points, join saddles, split saddles, or combined saddles.
- Construct join and split trees, optionally pruning degree-two nodes and retaining arc segmentations.
- Compute height-, volume-, or hypervolume-based branch decompositions.
- Build branch hierarchies and compare persistence-style pairs with bottleneck distance.
- Simplify a field by removing an extremum and perturbing scalar values while preserving a consistent vertex order.
- Inspect fields, trees, segmentations, branches, and point links with PyVista and Matplotlib helpers.

## Requirements

- Python 3
- The packages listed in [`requirements.txt`](requirements.txt)
- A graphical or notebook environment for interactive plots

Tree-layout visualizations use NetworkX's PyGraphviz integration. To call methods such as `tree.visualize()` or `branch_decomposition.visualize()`, install the Graphviz system package and `pygraphviz` in addition to the repository requirements:

```bash
python -m pip install pygraphviz
```

Computational APIs do not require Graphviz unless one of those layout helpers is called.

## Installation

Clone the repository, create a virtual environment, and install its dependencies:

```bash
git clone https://github.com/kamakshidasan/silpy.git
python3 -m venv silpy/.venv
source silpy/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r silpy/requirements.txt
```

## Quick start

The following example creates a reproducible synthetic scalar field, analyzes its critical points, builds a join tree, and computes a height-based branch decomposition.

```python
import random

from silpy import BranchDecomposition, BranchPathChecker, CriticalManager, Field, FieldAnalyzer, JoinTree


def main():
    random.seed(7)

    field = Field.from_random_gaussians(
        mode="mixed",
        num_gaussians=8,
        width=64,
        height=64,
        minimum_sigma=2,
        maximum_sigma=8,
    )

    field_analysis = FieldAnalyzer(field, "gaussian")
    critical_manager = CriticalManager(field_analysis)
    join_tree = JoinTree(critical_manager, prune=False, segmentation=True)
    branch_decomposition = BranchDecomposition(join_tree, scheme="height")

    print(f"Critical points: {len(field_analysis.critical_points)}")
    print(f"Join-tree nodes: {join_tree.number_of_nodes()}")
    print(f"Join tree valid: {join_tree.check()}")
    print(f"Branches: {len(branch_decomposition.branches)}")
    print(f"Branch decomposition valid: {BranchPathChecker(branch_decomposition).is_branch_decomposition()}")

    field.plot(name="gaussian", warp=True, warp_scale=5.0)


if __name__ == "__main__":
    main()
```

Pass `SplitTree` instead of `JoinTree` to build the split tree. The `ReebTree` factory is also available when the tree type is selected dynamically:

```python
from silpy import ReebTree

merge_tree = ReebTree(critical_manager, tree_type="split", prune=True, segmentation=True)
```

## Working with an existing mesh

`Field` reads any format supported by `pyvista.read`. The selected scalar array must be point data on the mesh.

```python
from silpy import CriticalManager, Field, FieldAnalyzer, SplitTree

field = Field(filename="data/surface.vtk")
field_analysis = FieldAnalyzer(field, name="temperature")
critical_manager = CriticalManager(field_analysis)
split_tree = SplitTree(critical_manager, prune=True, segmentation=True)

print(split_tree.get_edges())
split_tree.plot(style="square", show_tree=True)
```

For a 2D NumPy array, use `FieldBuilder` directly when you need to control the scalar-array name:

```python
from silpy import Field, FieldBuilder

structured_grid = FieldBuilder.create_structured_grid(scalar_values, field_name="temperature")
surface_mesh = FieldBuilder.triangulate(structured_grid, field_name="temperature")
field = Field(mesh=surface_mesh)
```

## Branch attributes and distances

Branch decomposition supports three schemes:

- `height`: absolute scalar difference between branch endpoints
- `volume`: number of segmented points associated with an arc
- `hypervolume`: sum of scalar values over an arc's segmented points

Volume and hypervolume require segmentation. `BranchDecomposition` will compute the required segmentation when it is not already present.

```python
from silpy import BottleneckDistance, BranchDecomposition, BranchHierarchy

branch_decomposition = BranchDecomposition(join_tree, scheme="volume")
branch_hierarchy = BranchHierarchy(branch_decomposition)

comparison = BottleneckDistance(
    [(0.0, 0.7), (0.2, 0.9)],
    [(0.0, 0.6), (0.3, 1.0)],
)

print(comparison.distance)
comparison.print_matching()
```

`BottleneckDistance` accepts either raw `(birth, death)` scalar pairs or two merge-tree branch decompositions.

## Field simplification

`FieldSimplification` removes a selected minimum from a join-tree field or a selected maximum from a split-tree field. The result is available as `final_field`.

```python
from silpy import FieldSimplification

removable_minimum = critical_manager.minimums[0]
simplification = FieldSimplification(field, "gaussian", "join", removable_minimum)
simplified_field = simplification.final_field
simplified_field.save("simplified.vtk")
```

The simplification pipeline currently targets surface meshes and expects the selected extremum to have a parent in the corresponding tree.

## Project layout

| Path | Purpose |
| --- | --- |
| `field/` | Scalar-field construction, loading, and critical-point analysis |
| `point/` | Vertex representation and scalar/index ordering |
| `manager/` | Organization of critical points and join/split profiles |
| `tree/` | Tree data structures, merge-tree construction, and segmentation |
| `branch/` | Branch records, attributes, and decompositions |
| `hierarchy/` | Parent-child hierarchies over decomposed branches |
| `distances/` | Bottleneck distance and matching |
| `simplification/` | Field cutting, reordering, and extremum removal |
| `checker/` | Point- and tree-type predicates |
| `formatter/` | Compact scalar and coordinate labels for visualizations |
| `pathfinder/` | Parallel monotone-path discovery |
| `heap/` | Union-find and heap support for tree construction |
| `debug/` | PyVista, Matplotlib, and NetworkX visualization helpers |
| `tests/` | Runtime validators for merge trees and branch decompositions |
