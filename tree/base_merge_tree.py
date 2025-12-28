from ..tree.tree import Tree
from ..pathfinder.path_finder import PathFinder
from .segmentation import Segmentation
from ..heap.heap import UnionFind

class BaseMergeTree(Tree):
    def __init__(self, manager, type, contour=False, prune=False, segmentation=True):
        super().__init__(type)

        self.manager = manager
        self.type = type
        self.contour = contour
        self.prune = prune
        self.segmentation = segmentation

        self.build_merge_tree()

    def build_merge_tree(self):
        critical_points, scalar_values, link_field, index_field = self.load_profile()
        all_paths = PathFinder.find_all_monotone_paths(critical_points, link_field, index_field)
        self.construct_tree(scalar_values, critical_points, all_paths)

        if self.prune:
            self.prune_tree()

        if self.segmentation:
            self.find_segmentation()

    def construct_tree(self, scalars, critical_points, path_pairs):
        self.union_find = UnionFind(scalars, self.type)

        for source_index, target_index in path_pairs:
            representative = self.union_find.find(target_index)
            minimum_index = self.union_find.get_min(representative)

            if self.union_find.find(source_index) != self.union_find.find(minimum_index):
                self.add_edge(
                    critical_points[source_index],
                    critical_points[minimum_index]
                )
                self.union_find.union(source_index, minimum_index)

    def prune_tree(self):
        nodes = set(self.nodes())
        degree_two_nodes = {node for node in nodes if self.is_degree_two_node(node)}
        non_degree_two_nodes = list(nodes - degree_two_nodes)

        for node in degree_two_nodes:
            self.reduce_node(node, return_info=False)

        self.manager.set_mandatory_points(self.type, non_degree_two_nodes)

    def find_segmentation(self):
        self.arcs = Segmentation.find_merge_tree_segmentation(self)
