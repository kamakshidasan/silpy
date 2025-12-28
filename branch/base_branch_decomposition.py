from collections import defaultdict
from ..tree.tree import Tree
from ..branch.attribute_tree import AttributeTree
from ..branch.branch import BranchQueue, BranchCollection, Branch
from ..debug.branch import visualize_tree_pairs


class BaseBranchDecomposition(Tree):
    def __init__(self, scheme='height'):
        super().__init__()
        self.scheme = scheme
        self.queue = BranchQueue()
        self.branches = BranchCollection()
        self.pairs = []
        self.snapshots = []
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

    def record_snapshot(self, frame):
        self.snapshots.append(frame.duplicate())

    def reduce_trees(self, node):
        for tree in self.trees():
            tree.reduce_node(node)

    def refresh_trees(self):
        for tree in self.trees():
            tree.refresh()

    def reset(self):
        self.restore_structures()

        # set pairs for each snapshot
        for snapshot_index, snapshot in enumerate(self.snapshots):
            snapshot.pairs = self.pairs[snapshot_index:]
            snapshot.branches = self.branches[snapshot_index:]
            snapshot.values = self.values[snapshot_index:]
            snapshot.all_branches = self.branches

    def take_snapshots(self):
        pairs = self.pairs

        partners = defaultdict(set)
        for birth, death in pairs:
            partners[birth].add(death)
            partners[death].add(birth)

        frame = self.duplicate()

        # initially take that snapshot
        self.record_snapshot(frame)

        # attempt to remove each node in contour tree
        # except the last pair (because that would be the trunk)
        for birth, death in pairs[:-1]:
            partners[birth].remove(death)
            partners[death].remove(birth)

            # if a node does not have any partners remaining
            # you can reduce the node
            for node in (birth, death):
                if not partners[node]:
                    frame.reduce_trees(node)

            # get the attributes correctly
            frame.refresh_trees()

            # take a snapshot after node removal
            self.record_snapshot(frame)

        self.reset()


    def visualize(self, *positional_arguments, **keyword_arguments):
        return self.primary_tree.visualize(*positional_arguments, **keyword_arguments)

    def plot(self, *positional_arguments, **keyword_arguments):
        return self.primary_tree.plot(*positional_arguments, **keyword_arguments)


    def visualize_snapshots(self, step=0, crop=False, label=None, reverse=False, node_size=800, font_size=6, tree_type='contour'):
        if hasattr(self, 'snapshots'):
            assert -len(self.snapshots) <= step < len(self.snapshots)
            snapshot_index = step if crop else 0
            snapshot = self.snapshots[snapshot_index]

            if tree_type == 'merge':
                snapshot_tree = snapshot.merge_tree
            elif tree_type == 'join':
                snapshot_tree = snapshot.join_tree
            elif tree_type == 'split':
                snapshot_tree = snapshot.split_tree
            else:
                snapshot_tree = snapshot.contour_tree

            visualize_tree_pairs(snapshot_tree, self.pairs, step, label=label, reverse=reverse, node_size=node_size, font_size=font_size)
