import networkx as nx
import copy

from ..checker.tree_checker import is_merge
from ..debug.segmentation import plot_merge_tree_and_segmented_arcs
from ..debug.segmentation import plot_warpable_sphere_segmentation
from ..debug.tree import plot_warped_tree
from ..tests.tests import MergeTreeChecker
from ..tree.tree import Tree

class BaseTree:
    def __init__(self, manager, tree_type, prune=False, segmentation=True):
        super().__init__(manager, tree_type, prune, segmentation)

########################################################

    def duplicate(self):
        cloned = object.__new__(type(self))
        if isinstance(self, nx.DiGraph):
            nx.DiGraph.__init__(cloned)

        cloned.manager      = self.manager
        cloned.type         = self.type
        cloned.prune        = self.prune
        cloned.segmentation = self.segmentation

        cloned.add_nodes_from(self.nodes(data=True))
        cloned.add_edges_from(self.edges(data=True))

        # arcs is required for attribute manager in branch decomposition
        try:
            cloned.arcs = copy.copy(self.arcs)
        except AttributeError:
            cloned.arcs = None
            pass

        # join and split tree is needed for branch decomposition
        try:
            cloned.join_tree = self.join_tree.duplicate()
            cloned.split_tree = self.split_tree.duplicate()
        except AttributeError:
            pass

        return cloned

########################################################

    def check(self, **kwargs):
        if is_merge(self.type):
            return MergeTreeChecker(self).is_merge_tree(**kwargs)

########################################################

    def plot(self, mesh, style='tree', warp=False, warp_scale=8.0, show_tree=False, sphere_radius=0.7):
        if style == 'sphere':
            plot_warpable_sphere_segmentation(mesh, self.arcs, warp, warp_scale, sphere_radius)
        elif style == 'square':
            plot_merge_tree_and_segmented_arcs(mesh, self, self.arcs, show_tree=show_tree)
        else:
            plot_warped_tree(mesh, self, warp_scale=(warp_scale if warp else 0.0))

########################################################
