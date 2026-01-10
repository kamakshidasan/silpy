from .profile_loader import ProfileLoader


class JoinTree(ProfileLoader):
    def __init__(self, manager, prune=False, segmentation=True):
        super().__init__(manager, 'join', prune, segmentation)


class SplitTree(ProfileLoader):
    def __init__(self, manager, prune=False, segmentation=True):
        super().__init__(manager, 'split', prune, segmentation)
