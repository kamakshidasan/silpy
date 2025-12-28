from .base_tree  import BaseTree
from .base_merge_tree import BaseMergeTree

class ProfileLoader(BaseTree, BaseMergeTree):
    profile = {}

    def __init__(self, manager, tree_type, contour=False, prune=False, segmentation=True):
        super().__init__(manager, tree_type, contour, prune, segmentation)

    def load_profile(self):
        points_attribute, scalars_attribute, link_field, index_field, reverse = self.profile[self.contour]
        critical_points = self.manager[points_attribute]
        scalar_values   = self.manager[scalars_attribute]
        if reverse:
            critical_points = list(reversed(critical_points))
            scalar_values   = list(reversed(scalar_values))
        return critical_points, scalar_values, link_field, index_field
