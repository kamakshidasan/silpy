import copy
from collections import defaultdict
from ..tree.tree import Tree
from ..branch.base_branch_decomposition import BaseBranchDecomposition
from ..branch.attribute_tree import AttributeTree
from ..branch.branch import BranchQueue, BranchCollection, Branch
from ..debug.branch import visualize_tree_pairs

class MergeBranchDecomposition(BaseBranchDecomposition):
    def __init__(self, merge_tree, scheme='height', take_snapshots=True):
        super().__init__(scheme=scheme)

        self.merge_tree = merge_tree.duplicate()
        self.type = merge_tree.type
        self.original_tree = merge_tree

        self.initialize_tree()
        self.initialize_queue()
        self.compute_pairs()
        self.restore_structures()

        if take_snapshots:
            self.take_snapshots()

    def initialize_tree(self):

        # in case non-pruned tree is passed
        if not self.merge_tree.prune:
            self.merge_tree.prune_tree()
            self.merge_tree.prune = True

            if self.merge_tree.segmentation:
                self.merge_tree.find_segmentation()

            self.original_tree = self.merge_tree.duplicate()

        self.merge_tree.visualize()

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
        if not self.merge_tree.has_edge(parent, leaf):
            # find the correct parent now, and push to queue
            [parent] = self.merge_tree.get_parents(leaf)
            self.push_branch(leaf, parent, self.merge_tree)
            return

        self.remove_leaf(leaf, parent)
        self.reduce_parent(parent)

        self.record(leaf, parent, value, self.type)

    def remove_leaf(self, leaf, parent):
        # find the current attribute and add it to the node
        # in case there is a multi-saddle, adding it to the node will help us
        if self.merge_tree.segmentation:
            leaf_attribute = self.merge_tree.get_attribute(parent, leaf, self.scheme)
            self.merge_tree.nodes[parent][self.scheme] += leaf_attribute

        # now remove the leaf
        self.merge_tree.remove_node(leaf)

    def reduce_parent(self, parent):
        # if the parent is degree-2, then it can be removed
        if not self.merge_tree.is_degree_two_node(parent):
            return

        # we know that the parent is a degree-2
        # so definitely only one grandparent and child exist
        grandparent = self.merge_tree.get_parents(parent)[0]
        child = self.merge_tree.get_children(parent)[0]

        if self.merge_tree.segmentation:
            # get the attribute of grandparent-parent and parent-child
            grandparent_attribute = self.merge_tree.get_attribute(grandparent, parent, self.scheme)
            child_attribute = self.merge_tree.get_attribute(parent, child, self.scheme)

            # grandparent-child edge attributes
            new_attribute = grandparent_attribute + child_attribute

            # in case parent was a multi-saddle, it will have some residual value that needs to be added
            parent_attribute = self.merge_tree.nodes[parent][self.scheme]
            new_attribute = new_attribute + parent_attribute
        else:
            new_attribute = abs(grandparent.scalar - child.scalar)

        # ---------------------
        # reduce the parent, because it was degree-2
        self.merge_tree.reduce_node(parent)
        # ---------------------

        # only this edge would have changed, change its attribute
        self.merge_tree[grandparent][child][self.scheme] = new_attribute


    def compute_trunk_pair(self):
        # at the end there should be one pair
        # that wouldn't have gone into queue
        # because can_simplify wouldn't pass
        [root] = self.merge_tree.get_roots()
        [child] = self.merge_tree.get_children(root)
        pair = (root, child)
        value = self.merge_tree.get_attribute(root, child, self.scheme)
        self.record(root, child, value, self.type)

    # -------------------------------------------------------------------
    # Everything after this line is for taking snapshots


    def trees(self):
        return [self.merge_tree]

    def restore_structures(self):
        # go back to original state
        self.merge_tree = self.original_tree
        self.merge_tree = AttributeTree(self.merge_tree)
        self.primary_tree = self.merge_tree


    def duplicate(self):
        cloned = self.__class__.__new__(self.__class__)
        Tree.__init__(cloned)
        cloned.merge_tree = self.merge_tree.duplicate()
        cloned.type = self.type
        cloned.original_tree = self.original_tree
        cloned.scheme = self.scheme
        cloned.primary_tree = cloned.merge_tree # for visualization
        return cloned


    # i want
    def visualize_snapshots(self, *positional_arguments, **keyword_arguments):
        # make sure we only use the merge tree, but yeesh
        keyword_arguments['tree_type'] = 'merge'
        return super().visualize_snapshots(*positional_arguments, **keyword_arguments)
