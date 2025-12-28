import pyvista as pv
import networkx as nx
from itertools import combinations
import matplotlib.pyplot as plt
from silpy.debug.palette import get_color_palette, get_node_color

########################################################

# Given a point plot it and its upper/lower link
def plot_point(mesh_data, point, name=None, sphere_radius=0.1):
    plotter = pv.Plotter()

    point_index = point.index
    point_coordinates = mesh_data.points[point_index]
    point_sphere = pv.Sphere(radius=sphere_radius, center=point_coordinates)
    plotter.add_mesh(point_sphere, color="yellow", label="Selected Point")

    cells_containing_point = []
    for cell_index in range(mesh_data.n_cells):
        cell = mesh_data.get_cell(cell_index)
        if point_index in cell.point_ids:
            cells_containing_point.append(cell_index)

    for face_index in cells_containing_point:
        face_cell = mesh_data.extract_cells(face_index)
        plotter.add_mesh(face_cell, show_edges=True, edge_color="black", line_width=2, opacity=0.5)


    for neighbor in point.point_neighbors:
        neighbor_index = neighbor.index
        neighbor_coordinates = mesh_data.points[neighbor_index]
        sphere_color = "blue" if neighbor < point else "red"
        neighbor_sphere = pv.Sphere(radius=sphere_radius, center=neighbor_coordinates)
        plotter.add_mesh(neighbor_sphere, color=sphere_color, label=f"Neighbor {neighbor_index}")

    plotter.add_legend()
    plotter.view_xy()
    plotter.show()

########################################################

# Given a list of points in the Point class - plot them together
# Again this works only in 2 dimensions
def visualize_points_with_neighbors(points):
    plt.figure(figsize=(40, 16))

    node_positions = {}
    node_labels = {}
    node_outline_colors = {}

    # Store positions, labels, and outline colors
    for single_point in points:
        node_index = single_point.index
        node_x, node_y = single_point.coordinates[:2]
        node_positions[node_index] = (node_x, node_y)
        node_labels[node_index] = f"{node_index}\n{single_point.scalar:.3f}"
        node_outline_colors[node_index] = get_node_color(single_point.type)

    # Draw edges only between actual neighbors
    for single_point in points:
        x1, y1 = node_positions[single_point.index]
        for neighbor in single_point.point_neighbors:
            x2, y2 = node_positions[neighbor.index]
            plt.plot(
                [x1, x2],
                [y1, y2],
                linestyle='-',
                linewidth=2,
                color='black',
                zorder=1
            )

    # Draw nodes
    for node_index, (x, y) in node_positions.items():
        plt.scatter(
            [x],
            [y],
            s=1500,
            facecolors='white',
            edgecolors=node_outline_colors[node_index],
            linewidths=2,
            zorder=2
        )

    # Labels
    for node_index, (x, y) in node_positions.items():
        plt.text(
            x,
            y,
            node_labels[node_index],
            fontsize=10,
            ha='center',
            va='center',
            zorder=3
        )

    plt.gca().set_aspect('equal', adjustable='datalim')
    plt.axis('off')
    plt.show()

########################################################
