import networkx as nx
from ..checker.tree_checker import is_join, is_split
from ..tree.tree import Tree
from ..point.point import Point


class MergeTreeChecker(Tree):
    def __init__(self, merge_tree):
        super().__init__()
        self.merge_tree = merge_tree
        self.manager = merge_tree.manager

    def is_valid_internal_merge_node(self, node):
        return self.merge_tree.in_degree(node) == 1 and self.merge_tree.out_degree(node) >= 1

    def has_valid_internal_merge_nodes(self):
        return all(
            self.is_valid_internal_merge_node(internal_node)
            for internal_node in self.merge_tree.get_internal_nodes()
        )

    def is_connected(self):
        return self.merge_tree.is_connected()

    def has_single_heap(self):
        return len(self.merge_tree.union_find.heap_manager.heaps) == 1

    def has_same_roots(self, critical_points, root):
        expected_roots = {point for point in critical_points if point.type == root}
        return set(self.merge_tree.get_roots()) == expected_roots

    def has_same_leaves(self, critical_points, leaf):
        expected_leaves = {point for point in critical_points if point.type == leaf}
        return set(self.merge_tree.get_leaves()) == expected_leaves

    def is_merge_tree(self, debug=False):
        merge_trees = {
            "join": {
                "critical_points": self.manager.join_critical_points,
                "root": "maximum",
                "leaf": "minimum",
                "heap": self.merge_tree.is_max_heap,
            },
            "split": {
                "critical_points": self.manager.split_critical_points,
                "root": "minimum",
                "leaf": "maximum",
                "heap": self.merge_tree.is_min_heap,
            },
        }

        tree = merge_trees[self.merge_tree.type]
        critical_points = tree["critical_points"]
        root, leaf = tree["root"], tree["leaf"]

        same_roots = self.has_same_roots(critical_points, root)
        same_leaves = self.has_same_leaves(critical_points, leaf)
        heap_ordered = tree["heap"]()
        connected = self.is_connected()
        single_heap = self.has_single_heap()
        valid_internal_merge_nodes = self.has_valid_internal_merge_nodes()

        if debug:
            print("Same roots:", same_roots)
            print("Same leaves:", same_leaves)
            print("Heap ordered:", heap_ordered)
            print("Connected:", connected)
            print("Single heap:", single_heap)
            print("Valid internal merge nodes:", valid_internal_merge_nodes)

        return all([same_roots, same_leaves, heap_ordered, connected, single_heap, valid_internal_merge_nodes])


class BranchPathChecker:
    def __init__(self, branch_decomposition):
        self.branch_decomposition = branch_decomposition
        self.tree_type = branch_decomposition.type
        self.setup_tree()

    def setup_tree(self):
        self.tree = self.branch_decomposition.merge_tree
        if is_split(self.tree_type):
            self.path = self.split_path
        elif is_join(self.tree_type):
            self.path = self.join_path

    def join_path(self, birth, death):
        return nx.has_path(self.tree, death, birth)

    def split_path(self, birth, death):
        return nx.has_path(self.tree, birth, death)

    def all_paths_exist(self):
        for birth, death in self.branch_decomposition.branches.pairs:
            if not self.path(birth, death):
                return False
        return True

    def all_nodes_paired(self):
        paired_nodes = set()
        for birth, death in self.branch_decomposition.branches.pairs:
            paired_nodes.update((birth, death))
        return paired_nodes == set(self.tree.nodes())

    def is_branch_decomposition(self):
        return self.all_paths_exist() and self.all_nodes_paired()
