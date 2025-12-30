import networkx as nx
import heapq
from .tree           import Tree
from .base_tree      import BaseTree
from .merge_tree     import JoinTree, SplitTree
from .segmentation   import Segmentation

class BaseContourTree(Tree):
    def __init__(self, manager, type, contour=True, prune=False, segmentation=True):
        super().__init__(type)

        self.manager = manager
        self.type = type
        self.contour = contour
        self.prune = prune
        self.segmentation = segmentation

        self.build_contour_tree()

    def build_contour_tree(self):
        self.initialize_structures()
        self.reduce_all_leaves()
        self.restore_structures()

        if self.segmentation:
            self.find_segmentations()

    def initialize_structures(self):
        # you can initially set the segmentation to False
        # at the end you can find out segmentation for the non-pruned versions
        self.join_tree = JoinTree(self.manager, contour=True, segmentation=False)
        self.split_tree = SplitTree(self.manager, contour=True, segmentation=False)

        if self.prune:
            self.prune_trees()

        # duplicate merge trees
        self.original_join_tree  = self.join_tree.duplicate()
        self.original_split_tree = self.split_tree.duplicate()

        self.leaves, self.processed_leaves, self.queued_leaves = [], set(), set()

    def initialize_leaves(self):
        initial_leaves = self.join_tree.get_leaves() + self.split_tree.get_leaves()
        for leaf in initial_leaves:
            self.enqueue_node(leaf)

    def enqueue_node(self, node):
        if node not in self.processed_leaves and node not in self.queued_leaves:
            if self.join_tree.can_reduce_node(node) and self.split_tree.can_reduce_node(node):
                # you really don't need this check
                # but I want the queued_leaves to be always leaves
                if self.join_tree.is_valid_leaf(node) or self.split_tree.is_valid_leaf(node):
                    heapq.heappush(self.leaves, node)
                    self.queued_leaves.add(node)

    def reduce_all_leaves(self):
        self.initialize_leaves()

        while self.leaves:
            node = heapq.heappop(self.leaves)
            self.queued_leaves.remove(node)

            use_join_tree = self.join_tree.is_valid_leaf(node)
            use_split_tree = self.split_tree.is_valid_leaf(node)
            can_join_reduce = self.join_tree.can_reduce_node(node)
            can_split_reduce = self.split_tree.can_reduce_node(node)

            self.process_reduction(node, can_join_reduce, can_split_reduce, use_join_tree, use_split_tree)

    def process_reduction(self, node, can_join_reduce, can_split_reduce, use_join_tree, use_split_tree):
        self.processed_leaves.add(node)
        candidate_nodes = []
        candidate_nodes += self.add_join_edge(node, can_join_reduce, use_join_tree)
        candidate_nodes += self.add_split_edge(node, can_split_reduce, use_split_tree)
        for candidate in candidate_nodes:
            self.enqueue_node(candidate)

    def add_join_edge(self, node, can_join_reduce, use_join_tree):
        if not can_join_reduce:
            return []
        parents, children = self.join_tree.reduce_node(node)
        if use_join_tree and parents:
            self.add_edge(parents[0], node)
        return parents + children

    def add_split_edge(self, node, can_split_reduce, use_split_tree):
        if not can_split_reduce:
            return []
        parents, children = self.split_tree.reduce_node(node)
        if use_split_tree and parents:
            self.add_edge(node, parents[0])
        return parents + children

    def prune_trees(self):
        non_degree_two_nodes = []
        for critical_point in self.manager.contour_critical_points:
            is_join_degree_two = self.join_tree.is_degree_two_node(critical_point)
            is_split_degree_two = self.split_tree.is_degree_two_node(critical_point)

            if is_join_degree_two and is_split_degree_two:
                self.join_tree.reduce_node(critical_point)
                self.split_tree.reduce_node(critical_point)
            else:
                non_degree_two_nodes.append(critical_point)

        self.manager.set_mandatory_points(self.type, non_degree_two_nodes)

        # if called from outside
        self.prune = True

    def restore_structures(self):
        self.join_tree = self.original_join_tree
        self.split_tree = self.original_split_tree

        del self.leaves, self.processed_leaves, self.queued_leaves
        del self.original_join_tree, self.original_split_tree


    def find_segmentations(self):
        self.arcs = Segmentation.find_contour_tree_segmentation(self)

        # so always you will have merge tree segmentations
        # just remember these are the semi-pruned merge tree segmentations
        for merge_tree in [self.join_tree, self.split_tree]:
            merge_tree.find_segmentation()

        # if called from outside
        self.segmentation = True
