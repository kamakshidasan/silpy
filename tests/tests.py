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
        return (
            self.merge_tree.in_degree(node) == 1
            and self.merge_tree.out_degree(node) >= 1
        )

    def are_valid_internal_merge_nodes(self):
        for node in self.merge_tree.get_internal_nodes():
            if not self.is_valid_internal_merge_node(node):
                return False
        return True

    def is_merge_tree(self):
        merge_trees = {
            'join': {
                'critical_points': self.manager.join_critical_points,
                'root': 'maximum',
                'leaf': 'minimum',
                'heap': self.merge_tree.is_max_heap
            },
            'split': {
                'critical_points': self.manager.split_critical_points,
                'root': 'minimum',
                'leaf': 'maximum',
                'heap': self.merge_tree.is_min_heap
            }
        }

        tree = merge_trees[self.merge_tree.type]
        critical_points = tree['critical_points']
        expected_roots = {point for point in critical_points if point.type == tree['root']}
        expected_leaves = {point for point in critical_points if point.type == tree['leaf']}
        is_heap = tree['heap']

        return all([
            set(self.merge_tree.get_roots()) == expected_roots,
            set(self.merge_tree.get_leaves()) == expected_leaves,
            is_heap(),
            self.merge_tree.is_connected(),
            len(self.merge_tree.union_find.heap_manager.heaps) == 1,
            self.are_valid_internal_merge_nodes(),
        ])

class ContourTreeChecker(Tree):
    def __init__(self, contour_tree):
        super().__init__()
        self.contour_tree = contour_tree
        self.manager = contour_tree.manager

    def is_valid_internal_contour_node(self, node):
        in_degree_count = self.contour_tree.in_degree(node)
        out_degree_count = self.contour_tree.out_degree(node)
        return 1 <= in_degree_count <= 2 and 1 <= out_degree_count <= 2

    def are_valid_internal_contour_nodes(self):
        for node in self.get_internal_nodes():
            if not self.is_valid_internal_contour_node(node):
                return False
        return True

    def is_contour_tree(self):
        base_checks = (
            nx.is_directed_acyclic_graph(self.contour_tree)
            and len(list(nx.connected_components(self.contour_tree.to_undirected()))) == 1
            and self.contour_tree.is_max_heap()
            and all(
                self.is_valid_internal_contour_node(internal_node)
                for internal_node in self.contour_tree.get_internal_nodes()
            )
        )

        # if you want to test validity of a contour tree without a join and split tree
        try:
            critical_points = self.manager.contour_critical_points
        except AttributeError:
            return base_checks

        expected_roots = {point for point in critical_points if point.is_maximum()}
        expected_leaves = {point for point in critical_points if point.is_minimum()}

        return (
            base_checks
            and set(self.contour_tree.get_roots()) == expected_roots
            and set(self.contour_tree.get_leaves()) == expected_leaves
            and MergeTreeChecker(self.contour_tree.join_tree).is_merge_tree()
            and MergeTreeChecker(self.contour_tree.split_tree).is_merge_tree()
        )


class BranchPathChecker:
    def __init__(self, tree, branch_decomposition):
        self.tree = tree
        self.tree_type = self.tree.type
        self.branch_decomposition = branch_decomposition
        self._setup_path_method()

    def _setup_path_method(self):
        if is_split(self.tree_type):
            self._path = self._split_path
        elif is_join(self.tree_type):
            self._path = self._join_path
        elif is_contour(self.tree_type):
            self._path = self._contour_path

    def _join_path(self, birth, death):
        return nx.has_path(self.tree, death, birth)

    # just split is different
    def _split_path(self, birth, death):
        return nx.has_path(self.tree, birth, death)

    def _contour_path(self, birth, death):
        return nx.has_path(self.tree, death, birth)

    def all_paths_exist(self):
        for birth, death in self.branch_decomposition.branches.pairs:
            if not self._path(birth, death):
                return False
        return True

    def all_nodes_paired(self):
        paired_nodes = set()
        for birth, death in self.branch_decomposition.branches.pairs:
            paired_nodes.update((birth, death))
        return paired_nodes == set(self.tree.nodes())

    def is_branch_decomposition(self):
        return self.all_paths_exist() and self.all_nodes_paired()
