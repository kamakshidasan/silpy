from collections import defaultdict
from ..tree.tree import Tree
from ..branch.branch import BranchQueue, BranchCollection, Branch
from ..debug.branch import visualize_tree_pairs


class BaseBranchDecomposition(Tree):
    def __init__(self, scheme='height'):
        super().__init__()
        self.scheme = scheme
        self.queue = BranchQueue()
        self.branches = BranchCollection()
        self.pairs = []
        self.primary_tree = None

    def record(self, birth, death, value, type):
        branch = Branch(birth, death, value, type)
        self.branches.add(branch)

    def push_branch(self, leaf, parent, merge_tree):
        value = merge_tree.get_attribute(parent, leaf, self.scheme)
        branch = Branch(parent, leaf, value, merge_tree.type)
        self.queue.push(branch)

    def finalize_pairs(self):
        # after all pairs have been computed
        # then just have a final set of pairs and values
        # these are not duplicated
        self.pairs = self.branches.pairs
        self.branches = self.branches
        self.values = self.branches.values
        self.all_branches = self.branches

    # hide away this function
    def needs_volume(self):
        return self.scheme in ('volume', 'hypervolume')

    def visualize(self, *positional_arguments, **keyword_arguments):
        return self.primary_tree.visualize(*positional_arguments, **keyword_arguments)

    def plot(self, *positional_arguments, **keyword_arguments):
        return self.primary_tree.plot(*positional_arguments, **keyword_arguments)
