import networkx as nx
from ..heap.heap import UnionFind
from ..debug.tree import visualize_tree

# Adhitya: pretty proud of this class
class Tree(nx.DiGraph):
    def __init__(self, type=None):
        super().__init__()
        self.type = type

    def add_edge(self, u, v):
        super().add_edge(u, v)

    def has_node(self, node):
        return super().has_node(node)

    def has_edge(self, node1, node2):
        return super().has_edge(node1, node2)

    def is_leaf(self, node):
        return self.in_degree(node) == 1 and self.out_degree(node) == 0

    def is_root(self, node):
        return self.in_degree(node) == 0 and self.out_degree(node) == 1

    def is_internal(self, node):
        return not self.is_root(node) and not self.is_leaf(node)

    def is_valid_leaf(self, node):
        return self.has_node(node) and self.is_leaf(node)

    def is_degree_one_node(self, node):
        if node not in self.nodes:
            return False
        return self.in_degree(node) + self.out_degree(node) == 1

    def is_degree_two_node(self, node):
        if node not in self.nodes:
            return False
        return self.in_degree(node) == 1 and self.out_degree(node) == 1

    def is_connected(self):
        [root] = self.get_roots()
        reachable_count = len(nx.descendants(self, root)) + 1
        return reachable_count == len(self.nodes)

    def is_min_heap(self):
        for parent in self.nodes:
            for child in self.successors(parent):
                if child < parent:
                    return False
        return True

    def is_max_heap(self):
        for parent in self.nodes:
            for child in self.successors(parent):
                if child > parent:
                    return False
        return True

    def get_edges(self):
        return list(self.edges())

    def get_parents(self, node):
        if node not in self.nodes:
            return []
        return list(self.predecessors(node))

    def get_children(self, node):
        if node not in self.nodes:
            return []
        return list(self.successors(node))

    def get_leaves(self):
        nodes = [node for node in self.nodes if self.is_leaf(node)]
        return sorted(nodes)

    def get_roots(self):
        nodes = [node for node in self.nodes if self.is_root(node)]
        return sorted(nodes)

    def get_internal_nodes(self):
        nodes = [node for node in self.nodes if self.is_internal(node)]
        return sorted(nodes)

    def get_min_leaf(self):
        leaves = self.get_leaves()
        return min(leaves)

    def get_max_leaf(self):
        leaves = self.get_leaves()
        return max(leaves)

    def can_reduce_node(self, node):
        if node not in self.nodes:
            return False
        return self.in_degree(node) <= 1 and self.out_degree(node) <= 1

    def remove_node(self, node):
        super().remove_node(node)

    def reduce_node(self, node, return_info=True):
        if node not in self.nodes:
            return None
        parents = self.get_parents(node)
        children = self.get_children(node)
        for parent in parents:
            for child in children:
                self.add_edge(parent, child)
        self.remove_node(node)
        if return_info:
            return [parents, children]

    def visualize(self, label=None, reverse=False, use_node_type_colors=True, node_size=500, font_size=6):
        tree = nx.DiGraph(self) # yeesh
        visualize_tree(tree, label, reverse, use_node_type_colors, node_size, font_size)
