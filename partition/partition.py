import sys
import numpy as np
import pyvista as pv

from ..field.field_analyzer import FieldAnalyzer as OriginalFieldAnalyzer
from ..point.point import Point as OriginalPoint

# i have to partition the domain
# so for that we need to store this global_index variable
# we need to make sure this variable does not get lost in the partitions
# propagate that variable through FieldAnalyzer and Point
# it would have been slightly convenient to not do this monkey patching business
# and rather change the FieldAnalyzer and Point directly
# but Adhitya is Adhitya

class DomainPartitioner:
    def __init__(self, mesh, nx, ny):
        # compute global_index on the original mesh
        mesh.point_data["global_index"] = np.arange(mesh.n_points)

        unique_x_values = np.unique(mesh.points[:, 0])
        unique_y_values = np.unique(mesh.points[:, 1])

        x_boundaries_indices = np.round(np.linspace(0, unique_x_values.size - 1, nx + 1)).astype(int)
        y_boundaries_indices = np.round(np.linspace(0, unique_y_values.size - 1, ny + 1)).astype(int)

        x_boundaries = unique_x_values[x_boundaries_indices]
        y_boundaries = unique_y_values[y_boundaries_indices]

        centroids = mesh.cell_centers().points
        centroid_x_values = centroids[:, 0]
        centroid_y_values = centroids[:, 1]

        faces_array = mesh.faces.reshape(-1, 4)

        partitioned_meshes = {}

        for x_index in range(nx):
            x_min_value = x_boundaries[x_index]
            x_max_value = x_boundaries[x_index + 1]
            x_mask = ((centroid_x_values >= x_min_value) & (centroid_x_values <= x_max_value))

            for y_index in range(ny):
                y_min_value = y_boundaries[y_index]
                y_max_value = y_boundaries[y_index + 1]
                y_mask = ((centroid_y_values >= y_min_value) & (centroid_y_values <= y_max_value))

                cell_indices = np.where(x_mask & y_mask)[0]
                segment_faces = faces_array[cell_indices].ravel()

                segment_mesh = pv.PolyData(mesh.points, segment_faces)

                for data_name in mesh.point_data:
                    segment_mesh.point_data[data_name] = mesh.point_data[data_name]

                for cell_data_name in mesh.cell_data:
                    segment_mesh.cell_data[cell_data_name] = mesh.cell_data[cell_data_name][cell_indices]

                # remove orphan points and keep global_index aligned
                segment_mesh.clean(inplace=True)

                partitioned_meshes[(x_index, y_index)] = segment_mesh

        self.partitioned_meshes = partitioned_meshes

    @staticmethod
    def get_local(partitioned_mesh, global_index):
        global_indices_array = partitioned_mesh.point_data["global_index"]
        return np.where(global_indices_array == global_index)[0][0]

    @staticmethod
    def get_global(partitioned_mesh, local_index):
        global_indices_array = partitioned_mesh.point_data["global_index"]
        return global_indices_array[local_index]


#############

# If you are going to partition, you need to change FieldAnalyzer and Point as below
# I tried to monkeypatch it, but i didn't do it properly
# so for now i have commented it out

#############

# class FieldAnalyzer:
#     def __init__(self, field, name, domain_split=False):
#         self.mesh = field.mesh
#         self.name = name
#         self.process_mesh(domain_split)
#
#
#     def process_mesh(self, domain_split):
#         scalars = self.mesh.point_data[self.name]
#         if domain_split:
#             self.global_indices = self.mesh.point_data["global_index"]
#
#         points = self.initialize_points(self.mesh, scalars, domain_split)
#         for point in points.values():
#             self.compute_point_links(point)
#             self.classify_point(point)
#         self.points = points
#         self.critical_points = [point for point in points.values() if point.type != "regular"]
#
#
#     def initialize_points(self, mesh, scalar_values, domain_split):
#         faces = mesh.faces.reshape(-1, 4)
#         points = {}
#         for point_index in range(mesh.n_points):
#             coordinates = mesh.points[point_index]
#             global_index = self.global_indices[point_index] if domain_split else None
#             points[point_index] = OriginalPoint(point_index, scalar_values[point_index], coordinates, global_index)
#
#         for face_index, face_vertices in enumerate(faces):
#             _, p0, p1, p2 = face_vertices
#             for current, neighbor1, neighbor2 in [(p0, p1, p2), (p1, p2, p0), (p2, p0, p1)]:
#                 point = points[current]
#                 point.point_neighbors.add(points[neighbor1])
#                 point.point_neighbors.add(points[neighbor2])
#                 point.face_neighbors.add(face_index)
#
#         return points
#
# class Point:
#     def __init__(self, index, scalar, coordinates, global_index):
#         self.index = index
#         self.scalar = scalar
#         self.coordinates = tuple(coordinates)
#         self.point_neighbors = set()
#         self.face_neighbors = set()
#         self.lower_link = []
#         self.upper_link = []
#         self.link_graph = None
#         self.type = None
#         self.join_index = None
#         self.split_index = None
#         self.contour_index = None
#         self.global_index = global_index
#
#
#     def __str__(self):
#         return (
#             f"Point {self.index}\n"
#             f"Scalar: {self.scalar}\n"
#             f"Coordinates: {tuple(float(c) for c in self.coordinates)}\n"
#             f"Neighbors: {sorted(n.index for n in self.point_neighbors)}\n"
#             f"Lower link: {[sorted([p.index for p in comp]) for comp in self.lower_link]}\n"
#             f"Upper link: {[sorted([p.index for p in comp]) for comp in self.upper_link]}\n"
#             f"Split index: {self.split_index}\n"
#             f"Join index: {self.join_index}\n"
#             f"Type: {self.type.capitalize() if self.type else 'None'}\n"
#             f"Global Index: {self.global_index}\n"
#         )
