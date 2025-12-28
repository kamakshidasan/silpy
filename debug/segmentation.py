import pyvista as pv
import numpy as np
from ..debug.palette import get_color_palette
from ..debug.tree import plot_merge_tree

########################################################

def plot_segmented_arcs(mesh, arcs, plotter=None, point_size=35, show=True, window_size=(500, 500)):
    # Use provided plotter or create new
    if plotter is None:
        plotter = pv.Plotter(window_size=list(window_size))

    # Build arc point clouds
    arc_point_clouds = {}
    for arc, arc_nodes in arcs.items():
        node_indices = [node.index for node in arc_nodes]
        coordinates = mesh.points[np.array(node_indices)]
        arc_point_clouds[arc] = pv.PolyData(coordinates)

    # Assign distinct colors to each arc
    arc_colors = get_color_palette(
        number_of_colors=len(arc_point_clouds),
        base_palette_name="muted",
        max_base_colors=8
    )

    # Add each arc's point cloud
    for index, (arc, point_cloud) in enumerate(arc_point_clouds.items()):
        hex_color = arc_colors[index]
        plotter.add_mesh(
            point_cloud,
            color=hex_color,
            point_size=point_size,
            render_points_as_spheres=True
        )

    plotter.view_xy()
    if show:
        plotter.show(window_size=list(window_size))
    return plotter

########################################################

def plot_merge_tree_and_segmented_arcs(mesh, merge_tree, arcs, show_tree=False, point_size=35, window_size=(500, 500)):
    plotter = pv.Plotter(window_size=list(window_size))

    if arcs:
        plot_segmented_arcs(mesh, arcs, plotter=plotter, point_size=point_size, show=False, window_size=window_size)

    plotter.view_xy()
    plotter.show(window_size=list(window_size))
    return plotter


########################################################

def plot_warpable_sphere_segmentation(mesh, arcs, warp=False, warp_scale=8.0, sphere_radius=0.7, window_size=(500, 500)):

    # Determine mesh to plot (warped or original)
    mesh_to_plot = mesh.warp_by_scalar(factor=warp_scale) if warp else mesh

    # Initialize plotter
    plotter = pv.Plotter(window_size=list(window_size))
    plotter.show_axes()

    # Plot mesh
    plotter.add_mesh(mesh_to_plot, cmap="terrain", opacity=0.8, show_edges=False)

    # Prepare sphere glyph source
    sphere_source = pv.Sphere(radius=sphere_radius)

    # Generate color palette for arcs
    color_palette = get_color_palette(
        number_of_colors=len(arcs),
        base_palette_name="muted",
        max_base_colors=8
    )

    # Add glyph spheres for each arc
    for index, (arc, node_list) in enumerate(arcs.items()):
        node_indices = [node.index for node in node_list]
        coordinates = mesh_to_plot.points[np.array(node_indices)]
        point_cloud = pv.PolyData(coordinates)
        glyphs = point_cloud.glyph(geom=sphere_source, scale=False, orient=False)
        plotter.add_mesh(glyphs, color=color_palette[index])

    # Configure view and render
    plotter.view_xy()
    plotter.show(window_size=list(window_size))

########################################################
