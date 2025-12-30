from ..tree.tree import Tree
from collections import defaultdict
from ..branch.base_branch_decomposition import BaseBranchDecomposition
from ..branch.attribute_tree import AttributeTree
from ..branch.branch import BranchQueue, BranchCollection, Branch
from ..debug.branch import visualize_tree_pairs

class ContourBranchDecomposition(BaseBranchDecomposition):
    def __init__(self, contour_tree, scheme='height'):
        super().__init__(scheme=scheme)

        self.contour_tree = contour_tree.duplicate()
        self.type = contour_tree.type

        self.initialize_tree()
        self.initialize_queue()
        self.compute_pairs()
        self.restore_structures()

    def initialize_tree(self):
        # we *need* to prune a contour tree for branch decomposition
        if not self.contour_tree.prune:
            self.contour_tree.prune_trees()

            # if it was segmented before pruning -> need to recompute it
            if self.contour_tree.segmentation:
                self.contour_tree.find_segmentations()

        # attached to contour tree, so that it can be passed to attribute tree
        self.contour_tree.volume = self.needs_volume()

        # if branch decomposition needs volume and still not segmented
        if self.contour_tree.volume and not self.contour_tree.segmentation:
            self.contour_tree.find_segmentations()

        # after all states
        self.join_tree = self.contour_tree.join_tree
        self.split_tree = self.contour_tree.split_tree

        # save the original tree
        self.original_tree = self.contour_tree.duplicate()

        # once you prune the tree, find out the attributes
        # you will need this to push the attributes into a branch
        self.contour_tree = AttributeTree(self.contour_tree)
        self.join_tree = AttributeTree(self.join_tree)
        self.split_tree = AttributeTree(self.split_tree)


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
        if not current_tree.has_edge(saddle, leaf):
            return

        # no point trying to pair with a saddle that is already degree-2
        if current_tree.is_degree_two_node(saddle):
            return

        #print("leaf", leaf.index)

        self.accumulate_collapse(current_tree, saddle, leaf)

        current_tree.remove_node(leaf)

        self.prepare_collapse(other_tree, leaf)

        # ------------------
        # reduce the leaf, because it was degree-2
        other_tree.reduce_node(leaf)
        # ------------------

        self.apply_collapse(other_tree)

        # record just the pair for now -- it was definitely present
        self.record(saddle, leaf, value, tree_type)

        # attempt saddle reduction on both trees
        self.reduce_shared_saddle(current_tree, other_tree, saddle)


    def accumulate_collapse(self, merge_tree, saddle, leaf):
        # in case there is a multi-saddle, adding it to the node will help us
        if self.contour_tree.volume:
            leaf_attribute = merge_tree.get_attribute(saddle, leaf, self.scheme)
            merge_tree.nodes[saddle][self.scheme] += leaf_attribute


    def compute_attribute(self, merge_tree, node, child, grandparent):
        if self.contour_tree.volume:
            # In case node was a multi-saddle, it will have some residual value that needs to be added.
            node_contribution = merge_tree.nodes[node][self.scheme]
            child_contribution = merge_tree.get_attribute(node, child, self.scheme)
            grandparent_contribution = (
                merge_tree.get_attribute(grandparent, node, self.scheme) if grandparent else 0
            )
            return grandparent_contribution + child_contribution + node_contribution

        return abs(grandparent.scalar - child.scalar) if grandparent else 0


    def prepare_collapse(self, merge_tree, node):
        # node is degree-2 here, so exactly one parent and one child exist
        # (or)
        # node is the root of the other tree in which case grandparent does not exist

        parents = merge_tree.get_parents(node)
        child = merge_tree.get_children(node)[0]
        grandparent = parents[0] if parents else None

        new_attribute = self.compute_attribute(merge_tree, node, child, grandparent)

        # stash the grandparent-child update so we can apply it after we reduce the node
        merge_tree.pending_collapse = (grandparent, child, new_attribute)


    def apply_collapse(self, merge_tree):
        grandparent, child, new_attribute = merge_tree.pending_collapse

        if grandparent:
            merge_tree[grandparent][child][self.scheme] = new_attribute # replace
        else:
            merge_tree.nodes[child][self.scheme] += new_attribute # accumulate

        del merge_tree.pending_collapse


    def reduce_shared_saddle(self, current_tree, other_tree, saddle):
        # Reduce a saddle that is degree-2 in both trees
        if current_tree.is_degree_two_node(saddle):
            if other_tree.is_degree_two_node(saddle):
                #print("saddle", saddle.index)
                self.reduce_saddle(current_tree, saddle)
                self.reduce_saddle(other_tree, saddle)

                #current_tree.visualize(edge_attribute='volume')
                #other_tree.visualize(edge_attribute='volume')


    def reduce_saddle(self, merge_tree, saddle):
        # reduce a degree-2 saddle node in a merge tree
        # saddle is guaranteed that only one parent and one child exists
        # see if that parent + child can be a candidate to be pushed into queue

        self.prepare_collapse(merge_tree, saddle)

        [parents, children] = merge_tree.reduce_node(saddle)
        [parent], [child] = parents, children

        self.apply_collapse(merge_tree)

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


    def restore_structures(self):
        self.contour_tree = self.original_tree

        # you can have the attributes back again
        self.contour_tree = AttributeTree(self.contour_tree)
        self.contour_tree.join_tree = AttributeTree(self.contour_tree.join_tree)
        self.contour_tree.split_tree = AttributeTree(self.contour_tree.split_tree)

        self.join_tree = self.contour_tree.join_tree
        self.split_tree = self.contour_tree.split_tree
        self.primary_tree = self.contour_tree
