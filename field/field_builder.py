# field_builder.py
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

        n_x, n_y, _ = grid.dimensions
        num_points = n_x * n_y

        points = grid.points[:num_points]
        scalars_list = point_scalars[:num_points]

        triangles = []
        unique_edges = set()

        for y in range(n_y - 1):
            for x in range(1, n_x):
                p0 = (x - 1) + (y + 1) * n_x
                p1 = (x - 1) + y * n_x
                p2 = x + y * n_x
                p3 = x + (y + 1) * n_x

                triangles.append([3, p0, p1, p2])
                triangles.append([3, p0, p3, p2])

                for a, b in [(p0, p1), (p1, p2), (p2, p0), (p0, p3), (p3, p2), (p2, p0)]:
                    a, b = (a, b) if a < b else (b, a)
                    unique_edges.add((a, b))

        faces = np.array(triangles, dtype=np.int64).ravel()

        mesh = pv.PolyData(points, faces=faces)

        # i remember i implemented this for a specific reason
        # i think it was something in topological simplification
        # i am going to comment this for now

        # lines_list = []
        # for a, b in unique_edges:
        #     lines_list.append(2)
        #     lines_list.append(a)
        #     lines_list.append(b)
        # lines = np.array(lines_list, dtype=np.int64)
        #
        # mesh = pv.PolyData(points, faces=faces, lines=lines)

        mesh[field_name] = scalars_list
        return mesh

    @staticmethod
    def from_points(point_list, face_list, field_name="custom"):
        # Ensure row positions match logical indices: after this,
        # row i in points_array corresponds to Point.index == i
        point_list = sorted(point_list, key=lambda point: point.index)

        coordinate_list = [point.coordinates for point in point_list]
        scalar_value_list = [point.scalar for point in point_list]
        points_array = np.array(coordinate_list, dtype=float)

        # Faces: use the logical indices directly because they now match row positions
        flattened_faces_list = []
        for point_index_a, point_index_b, point_index_c in face_list:
            flattened_faces_list.extend([3, point_index_a, point_index_b, point_index_c])
        faces_array = np.array(flattened_faces_list, dtype=np.int64)

        # # Lines: collect undirected edges from neighbor relations using logical indices
        # edge_set = set()
        # for source_point in point_list:
        #     for neighbor_point in source_point.point_neighbors:
        #         edge_pair = tuple(sorted((source_point.index, neighbor_point.index)))
        #         edge_set.add(edge_pair)
        #
        # flattened_lines_list = []
        # for mesh_index_a, mesh_index_b in edge_set:
        #     flattened_lines_list.extend([2, mesh_index_a, mesh_index_b])
        # lines_array = np.array(flattened_lines_list, dtype=np.int64)
        # mesh = pv.PolyData(points_array, faces=faces_array, lines=lines_array)

        mesh = pv.PolyData(points_array, faces=faces_array)
        mesh[field_name] = np.array(scalar_value_list, dtype=float)
        return mesh
