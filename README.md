# Datasheet Graph Picker

App that makes it easy to retrieve graph data from technical datasheets.

---

Author: Guilherme M Bertolino

## Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+O` | Open image |
| `Ctrl+R` | Reset view |
| `Ctrl+N` | Add graph |
| `Ctrl+Delete` | Remove active graph |
| `Ctrl+E` | Export active graph as CSV |
| `Ctrl+Shift+E` | Export all graphs as CSV |
| `Ctrl+M` | Toggle magnifier |
| `Ctrl+Z` | Remove the last point from the active graph |

`Ctrl+Z` can be repeated to remove multiple points in reverse order.

## Interpolation

After selecting at least two points in a graph, click `Interpolate`. Enter the
start value `x0`, the end value `xf`, and the total number of points. The app
creates a new graph with values interpolated linearly between the selected
points.

## Point editing

In points mode, drag a point directly on the graph to move it. Select a point
in the tree and click `Remove point` to delete it. Points can also be dragged
inside their graph in the tree to change their order in the curve.
