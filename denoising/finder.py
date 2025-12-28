from ..field.field_analyzer import FieldAnalyzer
from ..debug.point import visualize_points_with_neighbors
import numpy as np

class Finder3D:
    def __init__(self, order_points, saddle, extremum):
        self.original_points = order_points
        self.saddle = saddle
        self.saddle_index = saddle.index
        self.extremum = extremum
        self.extremum_type = extremum.type

    # small central helpers
    def get_field_points(self, field, field_name="order"):

        #print(field.mesh.array_names)

        field_data = FieldAnalyzer(field, field_name)
        return field_data.points

    def get_extremums(self, field_points, extremum_type):
        return [point for point in field_points.values() if point.type == extremum_type]

    @staticmethod
    def visualize(field, field_name="order"):
        field_data = FieldAnalyzer(field, field_name)
        field_points = list(field_data.points.values())
        visualize_points_with_neighbors(field_points)


    def get_boundary_points(self, field, field_points):
        surface_polydata = field.mesh.extract_surface()
        boundary_indices = np.asarray(surface_polydata.point_data["silpyIndex"])
        boundary_indices_set = set(boundary_indices)

        # discard the saddle itself so it cannot be chosen
        # apparently this could cause some issue according to a GitHub comment
        boundary_indices_set.discard(self.saddle_index)

        return [field_points[point_index] for point_index in boundary_indices_set]


    # given a list of extremum points
    # find out whether they are legal or not
    # by checking whether they exist on the boundary
    def find_legal_extremum_points(self, extremum_points):
        legal_extremum_points = []
        for extremum_point in extremum_points:
            original_point = self.original_points[extremum_point.index]

            # if the current point and original point have the same neighbors
            # then the point is on the interior
            if extremum_point.point_neighbors != original_point.point_neighbors:

                # and the original point was not on the boundary
                if not original_point.boundary:
                    legal_extremum_points.append(extremum_point)

        return legal_extremum_points

    # either return legal interior extremums,
    # or, if there are none, return a single boundary choice (min/max) instead
    def get_domain_extremums(self, field, extremum_type, boundary_selector):
        field_points = self.get_field_points(field)
        candidate_points = self.get_extremums(field_points, extremum_type)
        legal_points = self.find_legal_extremum_points(candidate_points)

        # Adhitya: this is a condition that is mentioned in the blog
        # if there are no legal minimum/maximum points, pick one on the boundary that is not the saddle
        if not legal_points:
            boundary_points = self.get_boundary_points(field, field_points)

            # pick based on min/max
            boundary_point = boundary_selector(boundary_points)
            legal_points = [boundary_point]

        return legal_points

    # combined version used by both public methods below
    def get_saddle_extremum(self, field, extremum_type):
        field_points = self.get_field_points(field).values()
        extremum_points = [point for point in field_points if point.type == extremum_type]
        extremum_indices = {point.index: point for point in extremum_points}
        saddle_extremum = extremum_indices[self.saddle_index]
        return saddle_extremum

    # keep public API the same
    def find_legal_maximum(self, field):
        return self.get_saddle_extremum(field, "maximum")

    def find_legal_minimum(self, field):
        return self.get_saddle_extremum(field, "minimum")

    # find all minimums that are valid
    def find_legal_minimums(self, field):
        return self.get_domain_extremums(field, "minimum", min)

    # find all maximums that are valid
    def find_legal_maximums(self, field):
        return self.get_domain_extremums(field, "maximum", max)

    def is_field_sufficient(self, field):
        field_points = self.get_field_points(field)

        minimum_points = self.get_extremums(field_points, "minimum")
        maximum_points = self.get_extremums(field_points, "maximum")

        legal_minimum_points = self.find_legal_extremum_points(minimum_points)
        legal_maximum_points = self.find_legal_extremum_points(maximum_points)

        all_legal_minimum_points = len(legal_minimum_points) == len(minimum_points)
        all_legal_maximum_points = len(legal_maximum_points) == len(maximum_points)

        if self.extremum_type == "maximum":
            exactly_one_legal_maximum_point = len(legal_maximum_points) == 1
            all_legal_maximum_points = all_legal_maximum_points and exactly_one_legal_maximum_point
        elif self.extremum_type == "minimum":
            exactly_one_legal_minimum_point = len(legal_minimum_points) == 1
            all_legal_minimum_points = all_legal_minimum_points and exactly_one_legal_minimum_point

        #visualize_points_with_neighbors(list(field_points.values()))
        #print(f"Maximum: {all_legal_maximum_points}; Minimum: {all_legal_minimum_points}")

        return all_legal_minimum_points and all_legal_maximum_points
