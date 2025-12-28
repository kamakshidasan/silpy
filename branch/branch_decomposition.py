from .contour_branch_decomposition import ContourBranchDecomposition
from .merge_branch_decomposition import MergeBranchDecomposition
from ..tree.merge_tree import JoinTree, SplitTree
from ..tree.contour_tree import ContourTree
from ..branch.attribute_tree import AttributeTree
from ..checker.tree_checker import TreeChecker


class BranchDecomposition:
    def __init__(self, tree, *args, **kwargs):
        if isinstance(tree, (JoinTree, SplitTree)):
            decomposer_class = MergeBranchDecomposition
        elif isinstance(tree, ContourTree):
            decomposer_class = ContourBranchDecomposition
        elif isinstance(tree, AttributeTree):
            if TreeChecker.is_merge(tree.type):
                decomposer_class = MergeBranchDecomposition
            else:
                decomposer_class = ContourBranchDecomposition

        self.__class__ = decomposer_class
        decomposer_class.__init__(self, tree, *args, **kwargs)
