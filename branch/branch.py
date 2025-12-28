import heapq
from ..checker.tree_checker import is_join, is_split
from ..debug.branch import visualize_pairs_bar_graph
from ..debug.branch import visualize_pairs_line_chart
from ..debug.branch import visualize_pairs_scatter_plot


class Branch:
    def __init__(self, node1, node2, value, type):
        self.birth, self.death = self.arrange_nodes(node1, node2)
        self.value = value
        self.type = type

    def arrange_nodes(self, node1, node2):
        return (node1, node2) if node1 < node2 else (node2, node1)

    def get_edge(self):
        edge_order = {
            'split': (self.death, self.birth),
            'join': (self.birth, self.death)
        }
        return edge_order[self.type]

    def __lt__(self, other):
        return (self.value, self.birth, self.death, self.type) < \
               (other.value, other.birth, other.death, other.type)

    def __eq__(self, other):
        return (self.birth == other.birth and
                self.death == other.death and
                self.type == other.type)

    def __hash__(self):
        return hash((self.birth, self.death, self.type))

    def __repr__(self):
        return (f"({self.birth.index}, {self.death.index}) [{self.value}] -> {self.type}")


class BranchQueue:
    def __init__(self):
        self.heap = []
        self.processed = set()

    def can_simplify(self, branch):
        birth, death = branch.birth, branch.death
        type = branch.type

        can_simplify_join = (is_join(type) and birth.is_minimum() and death.is_join_or_both())
        can_simplify_split = (is_split(type) and birth.is_split_or_both() and death.is_maximum())

        return can_simplify_join or can_simplify_split

    def push(self, branch):
        if branch not in self.processed and self.can_simplify(branch):
            heapq.heappush(self.heap, branch)
            self.processed.add(branch)

    def pop(self): return heapq.heappop(self.heap)
    def clear(self): self.heap.clear(); self.processed.clear()
    def __len__(self): return len(self.heap)
    def __repr__(self): return repr(self.heap)


class BranchCollection:
    def __init__(self):
        self.items = []
        self.pairs = []
        self.values = []
        self.processed = set()

    def add(self, branch):
        if branch not in self.processed:
            self.items.append(branch)
            self.pairs.append((branch.birth, branch.death))
            self.values.append(branch.value)
            self.processed.add(branch)

    def __len__(self): return len(self.items)
    def __getitem__(self, index): return self.items[index]

    def visualize(self, style='bar', step=0, crop=False, show_labels=True):
        if style == 'bar':
            visualize_pairs_bar_graph(self.pairs, self.values, step, crop, show_labels)
        elif style == 'line':
            visualize_pairs_line_chart(self.pairs, self.values, step, crop, show_labels)
        elif style == 'scatter':
            # NOTE: I figured that this can only support height for now
            # So even if you have the values of a different branch decomposition
            # only the pairing shown will be different
            visualize_pairs_scatter_plot(self.pairs, step, crop, show_labels, 'scalar')
