import networkx as nx
from ..tree.tree import Tree
from ..tree.base_tree import BaseTree
from ..checker.tree_checker import is_merge
from ..tree.segmentation import Segmentation
from ..debug.branch import visualize_attribute_tree

# TreeWrapper wraps Tree
# Tree.__init__ sets up the nx.DiGraph and assigns the type
# TreeWrapper keeps the same init signature as BaseTree,
# so AttributeTree can forward arguments properly
class TreeWrapper(Tree):
    def __init__(self, manager, tree_type, prune, segmentation):
        super().__init__(tree_type)

class AttributeTree(BaseTree, TreeWrapper):
    def __init__(self, source):
        super().__init__(source.manager, source.type, source.prune, source.segmentation)

        # copy all attributes from source into self
        self.__dict__.update(source.__dict__)

        self.add_nodes_from(source.nodes(data=True))
        self.initialize_node_attributes()

        for start_node, end_node in source.edges():
            attributes = self.compute_attributes(start_node, end_node)
            self.add_edge(start_node, end_node, **attributes)

    # Tree already has add_edge
    # this function overrides that one, with the attributes parameter included
    def add_edge(self, start_node, end_node, **attributes):
        nx.DiGraph.add_edge(self, start_node, end_node, **attributes)

    def get_attribute(self, source_node, target_node, attribute):
        return self[source_node][target_node][attribute]

    # testing to see if i can get attribute value of all edges
    def get_attribute_values(self, attribute_name):
            edge_attribute_values = {}
            for start_node, end_node in self.edges():
                edge_attribute_values[(start_node, end_node)] = self[start_node][end_node][attribute_name]
            return edge_attribute_values

    def initialize_node_attributes(self):
        for node in self.nodes():
            self.nodes[node]["height"] = 0
            self.nodes[node]["volume"] = 0
            self.nodes[node]["hypervolume"] = 0


    def compute_attributes(self, node_a, node_b):
        attributes = {}
        attributes["height"] = abs(node_a.scalar - node_b.scalar)
        # if a segmentation scheme was required, this would be set
        if self.segmentation:
            augmented_nodes = self.arcs[(node_a, node_b)]
            attributes["volume"] = len(augmented_nodes)
            attributes["hypervolume"] = sum(node.scalar for node in augmented_nodes)
        return attributes


    def visualize(self, edge_attribute='height', pairs=None, label=None, reverse=False, use_node_type_colors=True, node_size=500, font_size=6, edge_width=4.0):
        tree = nx.DiGraph(self) # yeesh

        # if hasattr(self, "arcs"):
        #     tree.arcs = self.arcs

        visualize_attribute_tree(tree, edge_attribute, pairs, label, reverse, use_node_type_colors, node_size, font_size, edge_width)
