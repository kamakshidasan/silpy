from .point_types import get_point_type
from ..point.point import Point
from .neighbor_indices import get_neighbor_indices



class PointProcessor:

    @staticmethod
    def make_components(bit_mask):
        components = []
        current_component = []

        for index in range(6):
            if (bit_mask >> index) & 1:
                current_component.append(index)
            else:
                if current_component:
                    components.append(current_component)
                    current_component = []

        if current_component:
            components.append(current_component)

        if len(components) > 1:
            if (bit_mask & 1) and ((bit_mask >> 5) & 1):
                components[0] = components[-1] + components[0]
                components.pop(-1)

        return components

    def build_points(self):
        point_indices, coordinates, scalars = self.indices, self.mesh.points, self.scalars

        points = {}
        critical_points = []

        for point_index, coordinate, scalar, point_type, is_critical, link_mask, neighbor_mask in zip(
            point_indices, coordinates, scalars, self.point_types, self.critical_flags, self.link_masks, self.neighbor_masks
        ):
            point_index, scalar = int(point_index), float(scalar)

            point = Point(point_index, scalar, coordinate)
            point.type = get_point_type(point_type)

            point.link_mask = link_mask
            point.neighbor_mask = neighbor_mask

            points[point_index] = point

            if is_critical:
                critical_points.append(point)

        self.points = points
        self.critical_points = critical_points

    def build_links(self):
        for point_index, point in self.points.items():
            neighbor_mask = int(point.neighbor_mask)
            link_mask = int(point.link_mask)

            upper_bits = link_mask & neighbor_mask
            lower_bits = (~link_mask) & neighbor_mask & self.SIX_BIT_MASK

            all_neighbors = get_neighbor_indices(point_index, self.width)

            upper_components = self.make_components(upper_bits)
            lower_components = self.make_components(lower_bits)

            point.upper_link = [[self.points[all_neighbors[index]] for index in component] for component in upper_components]
            point.lower_link = [[self.points[all_neighbors[index]] for index in component] for component in lower_components]

            neighbor_list = [neighbor_point for component in point.upper_link for neighbor_point in component]
            neighbor_list += [neighbor_point for component in point.lower_link for neighbor_point in component]
            point.point_neighbors = set(neighbor_list)
