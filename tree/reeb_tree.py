from .merge_tree import JoinTree, SplitTree

# why didn't I think of this before!
# join tree, split tree and contour tree all in one place
# ok, i've only tested this once
class ReebTree:
    def __new__(class_object, manager, tree_type, prune=True, segmentation=True):
        if tree_type == 'join':
            return JoinTree(manager, prune=prune, segmentation=segmentation)
        if tree_type == 'split':
            return SplitTree(manager, prune=prune, segmentation=segmentation)
