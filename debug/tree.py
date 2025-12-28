import pyvista as pv
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from ..formatter.value_formatter import ValueFormatter
from ..debug.palette import get_color_palette, get_node_color

########################################################

def visualize_tree(tree, label=None, reverse=False, use_node_type_colors=True, node_size=500, font_size=6):
    plt.figure()

    graph = nx.DiGraph(tree)

    if reverse:
        graph = graph.reverse(copy=False)

    layout_positions = nx.nx_agraph.graphviz_layout(graph, prog="dot")
    nodes = list(graph.nodes)

    if use_node_type_colors:
        node_color_list = [get_node_color(node_item.type) for node_item in nodes]
    else:
        palette = get_color_palette(
            number_of_colors=len(nodes),
            base_palette_name="muted",
            max_base_colors=20
        )
        node_color_list = palette

    label_key = label if label else 'index'
    label_mapping = {node_item: node_item.label(label_key) for node_item in nodes}

    nx.draw(
        graph,
        layout_positions,
        labels=label_mapping,
        node_color=node_color_list,
        with_labels=True,
        node_size=node_size,
        font_size=font_size,
        font_color='white'
    )
    plt.show()

########################################################


def plot_merge_tree(mesh, merge_tree, plotter=None, show=True, show_mesh=True, window_size=(500, 500)):
    if plotter is None:
        plotter = pv.Plotter(window_size=list(window_size))

    if show_mesh:
        plotter.add_mesh(mesh, cmap='viridis', show_edges=True, line_width=1.0, opacity=0.6)
        plotter.show_bounds(grid='back', location='outer', all_edges=True)
        plotter.show_axes()
        plotter.view_xy()

    diagonal_length = mesh.length
    sphere_radius = diagonal_length * 0.01

    for critical_point in merge_tree.nodes():
        point_coordinates = critical_point.coordinates
        sphere = pv.Sphere(
            radius=sphere_radius,
            center=point_coordinates,
            theta_resolution=16,
            phi_resolution=16
        )
        sphere_color = get_node_color(critical_point.type)
        plotter.add_mesh(sphere, color=sphere_color)

    for parent_node, child_node in merge_tree.edges():
        line_segment = pv.Line(
            pointa=parent_node.coordinates,
            pointb=child_node.coordinates
        )
        tube_segment = line_segment.tube(radius=sphere_radius * 0.15)
        plotter.add_mesh(tube_segment, color='yellow')

    if show:
        plotter.view_xy()
        plotter.show(window_size=list(window_size))
    return plotter

########################################################

def plot_warped_tree(mesh, merge_tree, warp_scale=8.0):

    if warp_scale == 0.0:
        warped_mesh = mesh.copy()
    else:
        warped_mesh = mesh.warp_by_scalar(factor=warp_scale)

    plotter = pv.Plotter(notebook=True, window_size=[500, 500])
    plotter.show_axes()

    plotter.add_mesh(warped_mesh, cmap="terrain", opacity=0.8, show_edges=False, pickable=False)

    for node in merge_tree.nodes:
        index = node.index
        warped_point = warped_mesh.points[index]

        sphere = pv.Sphere(radius=0.7, center=warped_point)
        sphere_color = get_node_color(node.type)
        sphere.field_data["name"] = [index]
        plotter.add_mesh(sphere, color=sphere_color)

    for node_a, node_b in merge_tree.edges:
        index_a, index_b = node_a.index, node_b.index
        point_a = warped_mesh.points[index_a]
        point_b = warped_mesh.points[index_b]

        line = pv.Line(pointa=point_a, pointb=point_b)
        tube = line.tube(radius=0.2)
        tube.field_data["name"] = [(index_a, index_b)]
        tube.field_data["type"] = ["edge"]
        plotter.add_mesh(tube, color="y")

    plotter.view_xy()
    plotter.show()

########################################################
