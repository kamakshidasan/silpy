from .base_contour_tree   import BaseContourTree
from .base_tree import BaseTree

class ContourTree(BaseTree, BaseContourTree):
    def __init__(self, manager, prune=False, segmentation=True):
        super().__init__(manager, 'contour', contour=True, prune=prune, segmentation=segmentation)
