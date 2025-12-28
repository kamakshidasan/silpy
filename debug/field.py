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

def resample_grid(unstructured_grid, samples_per_axis=40):
    bounds = unstructured_grid.bounds
    axis_mins = np.array([bounds[0], bounds[2], bounds[4]], dtype=float)
    axis_maxs = np.array([bounds[1], bounds[3], bounds[5]], dtype=float)
    axis_extents = axis_maxs - axis_mins


    longest_extent = float(axis_extents.max()) if axis_extents.max() > 0 else 1.0
    number_of_cells_array = np.maximum(1, np.round(samples_per_axis * axis_extents / longest_extent).astype(int))
    dimensions_array = number_of_cells_array + 1
    computed_spacing = np.where(number_of_cells_array > 0, axis_extents / number_of_cells_array, 1.0)

    dimension_x, dimension_y, dimension_z = [int(value) for value in dimensions_array]
    spacing_x, spacing_y, spacing_z = [float(value) for value in computed_spacing]

    image_grid = pv.ImageData(
        dimensions=(dimension_x, dimension_y, dimension_z),
        spacing=(spacing_x, spacing_y, spacing_z),
        origin=(axis_mins[0], axis_mins[1], axis_mins[2]),
    )

    sampled_image = image_grid.sample(unstructured_grid)
    return sampled_image

def plot_field_3d(mesh, name=None, cmap="coolwarm"):
    plotter = pv.Plotter(window_size=[500, 500])
    image_data = resample_grid(mesh, samples_per_axis=100)
    plotter.add_volume(image_data, scalars=name, cmap=cmap)
    plotter.show_bounds(grid="front", location="outer", all_edges=True)
    plotter.show_bounds(grid='back', location='outer', all_edges=True)
    plotter.show_axes()
    plotter.view_xy()
    plotter.show()
