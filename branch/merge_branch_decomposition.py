import copy
from collections import defaultdict
from ..tree.tree import Tree
from ..branch.base_branch_decomposition import BaseBranchDecomposition
from ..branch.attribute_tree import AttributeTree
from ..branch.branch import BranchQueue, BranchCollection, Branch
from ..debug.branch import visualize_tree_pairs

class MergeBranchDecomposition(BaseBranchDecomposition):
    def __init__(self, merge_tree, scheme='height'):
        super().__init__(scheme=scheme)

        self.merge_tree = merge_tree.duplicate()
        self.type = merge_tree.type
        self.original_tree = merge_tree

        self.initialize_tree()
        self.initialize_queue()
        self.compute_pairs()
        self.restore_structures()

    def initialize_tree(self):
        # in case non-pruned tree is passed
        self.merge_tree.prune_tree()

        # once you prune the tree, find out the attributes
        self.merge_tree = AttributeTree(self.merge_tree)


    def initialize_queue(self):
        self.queue.clear()

        # push all leaves to queue
        leaves = self.merge_tree.get_leaves()

        for leaf in leaves:
            [parent] = self.merge_tree.get_parents(leaf)
            self.push_branch(leaf, parent, self.merge_tree)

    def compute_pairs(self):
        while self.queue:
            branch = self.queue.pop()
            self.peel_branch(branch)

        self.compute_trunk_pair()
        self.finalize_pairs()

    def peel_branch(self, branch):
        leaf, parent = branch.get_edge()
        value = branch.value

        # we process priority queue lazily
        if self.merge_tree.has_edge(parent, leaf):
            self.merge_tree.remove_node(leaf)

            if self.merge_tree.is_degree_two_node(parent):
                self.merge_tree.reduce_node(parent)

            self.merge_tree.refresh()
            pair = (leaf, parent)
            self.record(leaf, parent, value, self.type)
        else:
            # find the correct parent now, and push to queue
            [parent] = self.merge_tree.get_parents(leaf)
            self.push_branch(leaf, parent, self.merge_tree)


    def compute_trunk_pair(self):
        # at the end there should be one pair
        # that wouldn't have gone into queue
        # because can_simplify wouldn't pass
        [root] = self.merge_tree.get_roots()
        [child] = self.merge_tree.get_children(root)
        pair = (root, child)
        value = self.merge_tree.get_attribute(root, child, self.scheme)
        self.record(root, child, value, self.type)


    def restore_structures(self):
        # go back to original state
        self.merge_tree = self.original_tree
        self.merge_tree = AttributeTree(self.merge_tree)
        self.primary_tree = self.merge_tree
