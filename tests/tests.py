import networkx as nx
from ..checker.tree_checker import is_join, is_split, is_contour
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


class ContourTreeChecker(Tree):
    def __init__(self, contour_tree):
        super().__init__()
        self.contour_tree = contour_tree
        self.manager = contour_tree.manager

    def is_valid_internal_contour_node(self, node):
        in_degree_count = self.contour_tree.in_degree(node)
        out_degree_count = self.contour_tree.out_degree(node)
        return 1 <= in_degree_count <= 2 and 1 <= out_degree_count <= 2

    def is_directed_acyclic(self):
        return nx.is_directed_acyclic_graph(self.contour_tree)

    def is_connected_undirected(self):
        return len(list(nx.connected_components(self.contour_tree.to_undirected()))) == 1

    def is_max_heap_ordered(self):
        return self.contour_tree.is_max_heap()

    def has_valid_internal_contour_nodes(self):
        return all(
            self.is_valid_internal_contour_node(internal_node)
            for internal_node in self.contour_tree.get_internal_nodes()
        )

    def has_same_roots(self, critical_points):
        expected_roots = {point for point in critical_points if point.is_maximum()}
        return set(self.contour_tree.get_roots()) == expected_roots

    def has_same_leaves(self, critical_points):
        expected_leaves = {point for point in critical_points if point.is_minimum()}
        return set(self.contour_tree.get_leaves()) == expected_leaves

    def is_join_merge_tree(self):
        return MergeTreeChecker(self.contour_tree.join_tree).is_merge_tree()

    def is_split_merge_tree(self):
        return MergeTreeChecker(self.contour_tree.split_tree).is_merge_tree()

    def is_contour_tree(self, multi=False, strict=False, debug=False):
        directed_acyclic = self.is_directed_acyclic()
        connected_undirected = self.is_connected_undirected()
        max_heap_ordered = self.is_max_heap_ordered()

        if multi:
            valid_internal_contour_nodes = True
        else:
            valid_internal_contour_nodes = self.has_valid_internal_contour_nodes()

        base_checks = directed_acyclic and connected_undirected and max_heap_ordered and valid_internal_contour_nodes

        if debug:
            print("Directed acyclic:", directed_acyclic)
            print("Connected (undirected):", connected_undirected)
            print("Max-heap ordered:", max_heap_ordered)
            print("Valid internal contour nodes:", valid_internal_contour_nodes)
            print("Base checks passed:", base_checks)

        if not strict:
            return base_checks

        try:
            critical_points = self.manager.contour_critical_points
        except AttributeError:
            return base_checks

        same_roots = self.has_same_roots(critical_points)
        same_leaves = self.has_same_leaves(critical_points)
        is_join_merge_tree = self.is_join_merge_tree()
        is_split_merge_tree = self.is_split_merge_tree()

        merge_checks = same_roots and same_leaves and is_join_merge_tree and is_split_merge_tree

        if debug:
            print("Same roots (expected maxima):", same_roots)
            print("Same leaves (expected minima):", same_leaves)
            print("Join tree is a merge tree:", is_join_merge_tree)
            print("Split tree is a merge tree:", is_split_merge_tree)
            print("Merge checks passed:", merge_checks)

        return base_checks and merge_checks


class BranchPathChecker:
    def __init__(self, tree, branch_decomposition):
        self.tree = tree
        self.tree_type = self.tree.type
        self.branch_decomposition = branch_decomposition
        self.setup_path_method()

    def setup_path_method(self):
        if is_split(self.tree_type):
            self.path = self.split_path
        elif is_join(self.tree_type):
            self.path = self.join_path
        elif is_contour(self.tree_type):
            self.path = self.contour_path

    def join_path(self, birth, death):
        return nx.has_path(self.tree, death, birth)

    # just split is different
    def split_path(self, birth, death):
        return nx.has_path(self.tree, birth, death)

    def contour_path(self, birth, death):
        return nx.has_path(self.tree, death, birth)

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
