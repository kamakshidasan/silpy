from .profile_loader import ProfileLoader

class JoinTree(ProfileLoader):
    profile = {
        False: ('join_critical_points', 'join_scalars', 'lower_link', 'join_index', False),
        True:  ('contour_critical_points','contour_scalars','lower_link','contour_index', False),
    }

    def __init__(self, manager, contour=False, prune=False, segmentation=True):
        super().__init__(manager, 'join', contour, prune, segmentation)

class SplitTree(ProfileLoader):
    profile = {
        False: ('split_critical_points',  'split_scalars',  'upper_link', 'split_index', False),
        True:  ('contour_critical_points','contour_scalars','upper_link','reversed_contour_index', True),
    }

    def __init__(self, manager, contour=False, prune=False, segmentation=True):
        super().__init__(manager, 'split', contour, prune, segmentation)
