import networkx as nx
import numpy as np
from collections import defaultdict
from itertools import combinations
from ..point.point import Point

class FieldAnalyzer:
    def __init__(self, field, name):
        self.mesh = field.mesh
        self.name = name
        self.critical_points = []
        self.index = "index"
        self.process_mesh()

    def process_mesh(self):
        # points is a dictionary, where each point is mapped to point index
        self.points = self.initialize_points(self.mesh, self.name)
        self.find_neighbors(self.mesh, self.points)
        self.analyze_all_points()

    # create a index array of points that persists extract cells
    def prepare_points(self, mesh):
        if self.index not in mesh.point_data:
            self.mesh.point_data[self.index] = np.arange(mesh.n_points, dtype=np.int64)

        return mesh.point_data[self.index]

    def initialize_points(self, mesh, scalar_name):
        point_indices = self.prepare_points(mesh)
        coordinates = mesh.points
        scalars = mesh.point_data[scalar_name]

        points = {}
        for point_index, coordinate, value in zip(point_indices, coordinates, scalars):
            point_object = Point(point_index, value, coordinate)
            points[point_index] = point_object

        return points

    def get_cell_neighbors(self, mesh):
        neighbors = []
        for cell_index in range(mesh.n_cells):
            cell = mesh.get_cell(cell_index)
            cell_point_indices = [int(point_id) for point_id in cell.point_ids]
            neighbors.append(cell_point_indices)
        return neighbors


    def find_neighbors(self, mesh, points):
        faces = self.get_cell_neighbors(mesh)
        original_ids = mesh.point_data[self.index]

        for face_index, face_vertices in enumerate(faces):
            vertex_indices = [int(original_ids[int(vertex_index)]) for vertex_index in face_vertices]
            for point1, point2 in combinations(vertex_indices, 2):
                points[point1].point_neighbors.add(points[point2])
                points[point2].point_neighbors.add(points[point1])

    def analyze_all_points(self):
        for point in self.points.values():
            self.compute_point_links(point)
            self.classify_point(point)

            if not point.is_regular():
                self.critical_points.append(point)


    def get_neighbour_ring(self, point):
        ring_nodes = set(point.point_neighbors)
        ring_edges = set()

        for neighbor1, neighbor2 in combinations(ring_nodes, 2):
            if (neighbor2 in neighbor1.point_neighbors) or (neighbor1 in neighbor2.point_neighbors):
                ring_edges.add((neighbor1, neighbor2))

        return ring_nodes, ring_edges

    def compute_point_links(self, point):
        neighbor_nodes, neighbor_edges = self.get_neighbour_ring(point)
        neighbor_graph = nx.Graph()
        neighbor_graph.add_edges_from(neighbor_edges)
        neighbor_graph.add_nodes_from(neighbor_nodes)

        upper_nodes = set()
        lower_nodes = set()
        for neighbor_point in neighbor_graph.nodes:
            if neighbor_point > point:
                upper_nodes.add(neighbor_point)
            else:
                lower_nodes.add(neighbor_point)

        edges_to_remove = [edge for edge in neighbor_graph.edges if (edge[0] in upper_nodes) ^ (edge[1] in upper_nodes)]
        neighbor_graph.remove_edges_from(edges_to_remove)
        point.link_graph = neighbor_graph

        point.lower_link = [list(component) for component in nx.connected_components(neighbor_graph.subgraph(lower_nodes))]
        point.upper_link = [list(component) for component in nx.connected_components(neighbor_graph.subgraph(upper_nodes))]

    def classify_point(self, point):
        lower_count = len(point.lower_link)
        upper_count = len(point.upper_link)

        if lower_count == 1 and upper_count == 0:
            classification = 'maximum'
        elif lower_count == 0 and upper_count == 1:
            classification = 'minimum'
        elif lower_count == 1 and upper_count == 1:
            classification = 'regular'
        elif lower_count == 1:
            classification = 'split'
        elif upper_count == 1:
            classification = 'join'
        else:
            classification = 'both'

        point.type = classification


    def get_sorted_points(self):
        all_points = list(self.points.values())
        sorted_points = sorted(all_points)
        return sorted_points
