from ..tree.tree import Tree
from collections import defaultdict
from ..branch.base_branch_decomposition import BaseBranchDecomposition
from ..branch.attribute_tree import AttributeTree
from ..branch.branch import BranchQueue, BranchCollection, Branch
from ..debug.branch import visualize_tree_pairs

class ContourBranchDecomposition(BaseBranchDecomposition):
    def __init__(self, contour_tree, scheme='height', take_snapshots=True):
        super().__init__(scheme=scheme)

        self.contour_tree = contour_tree.duplicate()
        self.type = contour_tree.type
        self.original_tree = contour_tree

        self.initialize_tree()
        self.initialize_queue()
        self.compute_pairs()
        self.restore_structures()

        if take_snapshots:
            self.take_snapshots()

    def initialize_tree(self):
        self.contour_tree.prune_trees()
        self.join_tree = self.contour_tree.join_tree
        self.split_tree = self.contour_tree.split_tree

        # once you prune the tree, find out the attributes
        # you will need this push the attributes into a branch
        self.contour_tree = AttributeTree(self.contour_tree)
        self.join_tree = AttributeTree(self.join_tree)
        self.split_tree  = AttributeTree(self.split_tree)


    def initialize_queue(self):
        self.queue.clear()

        # add leaves to the queue
        for merge_tree in [self.join_tree, self.split_tree]:
            for merge_leaf in merge_tree.get_leaves():
                [merge_parent] = merge_tree.get_parents(merge_leaf)
                self.push_branch(merge_leaf, merge_parent, merge_tree)

    def compute_pairs(self):
        while self.queue:
            branch = self.queue.pop()
            self.peel_branch(branch)

        self.compute_trunk_pair()
        self.finalize_pairs()


    def peel_branch(self, branch):
        # select the active and passive trees for peeling
        # find out which node acts as the saddle and which as the leaf
        merge_trees = {
            'join': (self.join_tree, self.split_tree),
            'split': (self.split_tree, self.join_tree),
        }

        tree_type, value = branch.type, branch.value

        current_tree, other_tree = merge_trees[tree_type]
        leaf, saddle = branch.get_edge()

        # only proceed if the edge exists
        if current_tree.has_edge(saddle, leaf):
            # no point trying to pair with a saddle that is already degree-2
            if not current_tree.is_degree_two_node(saddle):
                current_tree.remove_node(leaf)
                other_tree.reduce_node(leaf)

                # record just the pair for now -- it was definitely present
                self.record(saddle, leaf, value, tree_type)

                # attempt saddle reduction on both trees
                self.reduce_shared_saddle(current_tree, other_tree, saddle)


    def reduce_shared_saddle(self, current_tree, other_tree, saddle):
        # Reduce a saddle that is degree-2 in both trees
        if current_tree.is_degree_two_node(saddle):
            if other_tree.is_degree_two_node(saddle):
                self.reduce_saddle(current_tree, saddle)
                self.reduce_saddle(other_tree, saddle)


    def reduce_saddle(self, merge_tree, saddle):
        # reduce a degree-2 saddle node in a merge tree
        # saddle is guaranteed that only one parent and one child exists
        # see if that parent + child can be a candidate to be pushed into queue
        [parents, children] = merge_tree.reduce_node(saddle)
        [parent], [child] = parents, children

        # before pushing the branch, make sure there is a value to push
        merge_tree.refresh()

        self.push_branch(child, parent, merge_tree)


    def compute_trunk_pair(self):
        # both trees should be the same now (just inverted)
        # use the join tree because that represents a monotone descending path
        # In other words, it doesn't matter
        merge_tree = self.join_tree
        if merge_tree:
            [trunk_root] = merge_tree.get_roots()
            [trunk_leaf] = merge_tree.get_leaves()
            tree_type = merge_tree.type
            trunk_value = merge_tree.get_attribute(trunk_root, trunk_leaf, self.scheme)
            self.record(trunk_root, trunk_leaf, trunk_value, tree_type)


    # -------------------------------------------------------------------
    # Everything after this line is for taking snapshots


    def trees(self):
        return [
            self.contour_tree,
            self.contour_tree.join_tree,
            self.contour_tree.split_tree
        ]


    def restore_structures(self):
        self.contour_tree = self.original_tree

        # you can have the attributes back again
        self.contour_tree = AttributeTree(self.contour_tree)
        self.contour_tree.join_tree = AttributeTree(self.contour_tree.join_tree)
        self.contour_tree.split_tree  = AttributeTree(self.contour_tree.split_tree)

        self.join_tree = self.contour_tree.join_tree
        self.split_tree = self.contour_tree.split_tree
        self.primary_tree = self.contour_tree


    def duplicate(self):
        cloned = self.__class__.__new__(self.__class__)
        Tree.__init__(cloned)
        cloned.contour_tree = self.contour_tree.duplicate()
        cloned.type = self.type
        cloned.original_tree = self.original_tree
        cloned.scheme = self.scheme
        cloned.join_tree = cloned.contour_tree.join_tree
        cloned.split_tree = cloned.contour_tree.split_tree
        cloned.primary_tree = self.contour_tree # for visualization
        return cloned
