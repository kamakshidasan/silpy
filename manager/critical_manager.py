from ..debug.manager import plot_mesh_and_points


class CriticalManager:
    def __init__(self, field_data):

        # i really hope this is all i need
        # i am taking all points so that
        # i can use it for root-saddle segmentation in merge tree
        self.points = field_data.points
        self.critical_points = field_data.critical_points
        self.mesh = field_data.mesh

        self.maximums = []
        self.minimums = []
        self.join_saddles = []
        self.split_saddles = []

        # these will end up as single-element lists
        self.global_maximum = []
        self.global_minimum = []

        # arrays of critical points
        self.join_critical_points = []
        self.split_critical_points = []

        # arrays of scalar values
        self.join_scalars = []
        self.split_scalars = []

        self.join_mandatory_points = []
        self.split_mandatory_points = []

        self.separate_by_type()
        self.create_map()
        self.create_critical_point_lists()
        self.create_scalars()
        self.create_indices()

    def separate_by_type(self):
        for point in self.critical_points:
            if point.is_maximum():
                self.maximums.append(point)
            elif point.is_minimum():
                self.minimums.append(point)
            elif point.is_join():
                self.join_saddles.append(point)
            elif point.is_split():
                self.split_saddles.append(point)
            elif point.is_both():
                self.join_saddles.append(point)
                self.split_saddles.append(point)

    def sort_points(self, critical_points, reverse=False):
        # Rely entirely on Point.__lt__ / __gt__ / __eq__
        return sorted(critical_points, reverse=reverse)

    def create_map(self):
        # sort all of them here
        self.maximums = self.sort_points(self.maximums)
        self.minimums = self.sort_points(self.minimums)
        self.join_saddles = self.sort_points(self.join_saddles)
        self.split_saddles = self.sort_points(self.split_saddles)
        self.global_minimum = [self.minimums[0]]
        self.global_maximum = [self.maximums[-1]]

    def create_critical_point_lists(self):
        # the join critical points are already sorted during initialization
        # so just add them up
        join_minimums = self.minimums
        join_saddles = self.join_saddles
        self.join_critical_points = join_minimums + join_saddles + self.global_maximum

        # when you sort all points together,
        # it can happen that a saddle can appear before
        # all the maximums are completed
        # so good to sort individual types separately
        # and then add them up
        split_maximums = self.sort_points(self.maximums, reverse=True)
        split_saddles = self.sort_points(self.split_saddles, reverse=True)
        self.split_critical_points = split_maximums + split_saddles + self.global_minimum

    def create_scalars(self):
        self.join_scalars = [point.scalar for point in self.join_critical_points]
        self.split_scalars = [point.scalar for point in self.split_critical_points]

    def create_indices(self):
        join_points = self.join_critical_points
        for join_index, point in enumerate(join_points):
            point.join_index = join_index

        split_points = self.split_critical_points
        for split_index, point in enumerate(split_points):
            point.split_index = split_index

    def get_profile(self, tree_type):
        if tree_type == 'join':
            return self.join_critical_points, self.join_scalars
        elif tree_type == 'split':
            return self.split_critical_points, self.split_scalars


    def plot(self, mesh, points, name=None, cmap='viridis'):
        plot_mesh_and_points(mesh, points, name, cmap)
