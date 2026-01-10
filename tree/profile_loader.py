from .base_tree import BaseTree
from .base_merge_tree import BaseMergeTree


class ProfileLoader(BaseTree, BaseMergeTree):
    def __init__(self, manager, type, prune=False, segmentation=True):
        super().__init__(manager, type, prune, segmentation)

    def load_profile(self):
        critical_points, scalar_values = self.manager.get_profile(self.type)

        field_mapping = {
            'join':  ('lower_link', 'join_index'),
            'split': ('upper_link', 'split_index')
        }

        link_field, index_field = field_mapping[self.type]

        return critical_points, scalar_values, link_field, index_field
