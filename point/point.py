import numbers
from ..checker.point_checker import PointChecker
from ..formatter.value_formatter import ValueFormatter
from ..debug.point import plot_point
from ..debug.link import visualize_point_link_2d, visualize_point_link_circle

class Point(PointChecker):
    def __init__(self, index, scalar, coordinates):
        self.index = index
        self.scalar = scalar
        self.coordinates = tuple(coordinates)   # store (x, y, z)
        self.point_neighbors = set()      # holds Point instances
        self.lower_link = []
        self.upper_link = []
        self.link_graph = None # for visualization only
        self.type = None

        # I'm going to store split/join index here
        self.join_index = None
        self.split_index = None
        self.contour_index = None

        self.boundary = False


    def __str__(self):
        return (
            f"Point {self.index}\n"
            f"Scalar: {self.scalar}\n"
            f"Coordinates: {tuple(float(coordinate) for coordinate in self.coordinates)}\n"
            f"Neighbors: {sorted(neighbor.index for neighbor in self.point_neighbors)}\n"
            f"Lower link: {[sorted(point.index for point in component) for component in self.lower_link]}\n"
            f"Upper link: {[sorted(point.index for point in component) for component in self.upper_link]}\n"
            f"Split index: {self.split_index}\n"
            f"Join index: {self.join_index}\n"
            f"Type: {self.type.capitalize() if self.type else 'None'}\n"
        )

    def __repr__(self):
        return f"{self.index}"

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return self.index == other.index

    def __reduce__(self):
        # tell pickle how to rebuild me:
        # 1) call Point(index, scalar, coordinates)
        # 2) then restore the rest of my attributes
        return (
            self.__class__,
            (self.index, self.scalar, self.coordinates),
            self.__dict__
        )

    def __hash__(self):
        return hash(self.index)

    def __gt__(self, other):
        if self.scalar == other.scalar:
            return self.index > other.index
        return self.scalar > other.scalar

    def __lt__(self, other):
        if self.scalar == other.scalar:
            return self.index < other.index
        return self.scalar < other.scalar

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    # use this to allow attribute access via indexing
    # for example, mesh_points[index]['upper_link']
    def __getitem__(self, attribute_name):
        return getattr(self, attribute_name)

    # this function is used for generating a label
    # during split tree 2d visualization
    # in case if i give a "scalar" or "coordinate" as label attribute
    # it should not overflow the node circle
    def label(self, attribute_name):
        raw_value = self[attribute_name]
        return ValueFormatter.format(raw_value)

    def visualize(self, two_dimensional=True):
        if two_dimensional:
            visualize_point_link_2d(self)
        else:
            visualize_point_link_circle(self)

    def plot(self, mesh, sphere_radius=0.1):
        return plot_point(mesh, self, sphere_radius=sphere_radius)
