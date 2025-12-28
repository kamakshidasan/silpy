import pyvista as pv
from ..debug.palette import get_node_color

def plot_mesh_and_points(mesh, points, name=None, cmap='viridis'):
    plotter = pv.Plotter(window_size=[500, 500])

    first_name, *_ = mesh.point_data.keys()
    name = name if name is not None else first_name

    plotter.add_mesh(mesh, scalars=name, cmap=cmap, show_edges=True, line_width=1.0)

    # just during debugging for now
    
    #plotter.show_bounds(grid='back', location='outer', all_edges=True)
    #plotter.show_axes()
    plotter.view_xy()

    diagonal_length = mesh.length
    sphere_radius = diagonal_length * 0.015

    for point in points:
        center = point.coordinates
        sphere = pv.Sphere(
            radius=sphere_radius,
            center=center,
            theta_resolution=16,
            phi_resolution=16
        )
        plotter.add_mesh(
            sphere,
            color=get_node_color(point.type)
        )

    plotter.show()
