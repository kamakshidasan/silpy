import networkx as nx
from ..tree.tree import Tree
from .toporerry import Toporerry
from ..debug.hierarchy import visualize_branch_hierarchy

class BranchHierarchy(Toporerry):
    def __init__(self, branch_decomposition):
        self.branches = branch_decomposition.branches
        self.scheme = branch_decomposition.scheme
        self.type = branch_decomposition.type
        self.pairs = branch_decomposition.pairs
        self.values = branch_decomposition.values
        self.tree = self.get_tree(branch_decomposition)
        self.all_branches = branch_decomposition.all_branches

        self.branch_parent = {}
        self.branch_height = {}
        self.hierarchy_tree = Tree()

        self.build_hierarchy()

    def build_hierarchy(self):
        # 1) Map each endpoint‐pair to its monotone path
        pair_path = {}

        for branch in self.branches:
            child_node, parent_node = self.path_endpoints(branch)
            path = nx.shortest_path(self.tree, parent_node, child_node)
            pair_path[branch] = path


        # 2) Build a map for each point to which branch it belongs to (except the saddle)
        owner_branch = {}
        child_order = {}
        for branch, path in pair_path.items():
            for order, node in enumerate(path[1:-1]):
                owner_branch[node] = branch
                child_order[node] = order

        # 3) Build the tree of endpoint‐pairs
        for branch in self.branches:
            birth, death = branch.birth, branch.death
            owner_node = birth if birth in owner_branch else death

            # for root this will return None
            parent_branch = owner_branch.get(owner_node)
            self.branch_parent[branch] = parent_branch


            # attach the order of the branch also
            child_node = birth if birth in child_order else death
            branch.order = child_order.get(child_node, 0)

            # if parent_branch is not None, then add the edge
            parent_branch and self.hierarchy_tree.add_edge(parent_branch, branch)

        # 4) Get heights
        for branch in self.branches:
            branch.height = self.get_height(branch)


    def get_height(self, branch):
        if branch in self.branch_height:
            return self.branch_height[branch]

        parent_branch = self.branch_parent[branch]

        # this is for the root branch
        if parent_branch is None:
            self.branch_height[branch] = 0
        else:
            self.branch_height[branch] = self.get_height(parent_branch) + 1

        return self.branch_height[branch]

    def get_tree(self, branch_decomposition):
        if self.type == 'contour':
            return branch_decomposition.contour_tree
        else:
            return branch_decomposition.merge_tree


    def path_endpoints(self, branch):
        (birth, death) = branch.birth, branch.death
        edge_order = {
            'join':    (birth, death),
            'split':   (death, birth),
            'contour': (birth, death)
        }
        return edge_order[self.type]

    def visualize(self, step=0, branch_layout=False, label=None, reverse=False, node_size=2000):
        visualize_branch_hierarchy(self.hierarchy_tree, self.branches, self.all_branches, self.scheme, step, label, reverse, node_size)
