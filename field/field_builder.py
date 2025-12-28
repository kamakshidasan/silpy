import numpy as np
import pyvista as pv

class FieldBuilder:
    @staticmethod
    def create_structured_grid(matrix, field_name="gaussian"):
        # Create a PyVista structured grid from a 2D NumPy array
        rows, cols = matrix.shape

        # please don't ask why, but I guess y and then x in VTK file format
        y, x = np.meshgrid(np.arange(rows), np.arange(cols))
        z = np.zeros_like(x)  # z-coordinates are zero for a 2D scalar field

        grid = pv.StructuredGrid(x, y, z)
        grid.point_data[field_name] = matrix.flatten()

        return grid

    @staticmethod
    def triangulate(grid, field_name="gaussian"):
        # Given a PyVista StructuredGrid, return a PyVista mesh of triangles + lines
        point_scalars = grid.point_data[field_name]

        n_x, n_y, n_z = grid.dimensions
        num_points = n_x * n_y

        points = grid.points[:num_points]
        scalars_list = point_scalars[:num_points]

        triangles = []

        for y in range(n_y - 1):
            for x in range(1, n_x):
                p0 = (x - 1) + (y + 1) * n_x
                p1 = (x - 1) + y * n_x
                p2 = x + y * n_x
                p3 = x + (y + 1) * n_x

                triangles.append([3, p0, p1, p2])
                triangles.append([3, p0, p3, p2])

        faces = np.array(triangles, dtype=np.int64).ravel()

        mesh = pv.PolyData(points, faces=faces)
        mesh[field_name] = scalars_list
        return mesh
