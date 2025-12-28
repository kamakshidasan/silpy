import pyvista as pv
import numpy as np

########################################################

def plot_field(mesh, name=None, cmap="viridis"):
    plotter = pv.Plotter(window_size=[500, 500])
    plotter.add_mesh(mesh, scalars=name, cmap=cmap, show_edges=True, line_width=1.0)
    plotter.show_bounds(grid="back", location="outer", all_edges=True)
    plotter.show_axes()
    plotter.view_xy()
    plotter.show()

########################################################

def plot_warped_field(mesh, name=None, cmap="terrain", warp_scale=1.0):
    warped_mesh = mesh.warp_by_scalar(scalars=name, factor=warp_scale)
    plotter = pv.Plotter(window_size=[500, 500])
    plotter.add_mesh(
        warped_mesh,
        scalars=name,
        cmap=cmap,
        show_edges=True,
        line_width=1.0
    )
    plotter.view_xy()
    plotter.show()

########################################################
