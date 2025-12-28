import heapq
from copy import copy
from ..checker.tree_checker import is_join
from ..debug.heap import visualize_heap_manager, visualize_union_find

class HeapElement:
    def __init__(self, index, value, invert):
        # for join-tree, value is pre-negated to simulate a max-heap
        # for split-tree, value remains as-is to use min-heap behavior
        self.index = index
        self.invert = invert
        self.multiplier = -1 if self.invert else 1
        self.value = self.multiplier * value

    def __lt__(self, other):
        # compare values first
        if self.value == other.value:
            return self.index > other.index
        else:
            return self.value < other.value

    def __repr__(self):
        return f"({self.value}, {self.index})"

    __str__ = __repr__

class HeapManager:
    def __init__(self, values, type):
        # Set up heaps based on the tree argument
        self.type = type
        self.heaps = {}

        for merge_index, node_value in enumerate(values):
            # inversion only for join-tree, split-tree uses original value
            invert = is_join(type)
            heap_element = HeapElement(merge_index, node_value, invert)
            self.heaps[merge_index] = [heap_element]

    def merge_heaps(self, root_main, root_sub):
        for value in self.heaps[root_sub]:
            heapq.heappush(self.heaps[root_main], value)
        del self.heaps[root_sub]  # Remove the sub-heap for memory efficiency

    def get_min(self, root):
        node_root = self.heaps[root][0] # gets both value and index
        return node_root.index

    def duplicate(self):
        cloned = copy(self)
        heaps = {
            node_index: [copy(heap_element) for heap_element in heap_list]
            for node_index, heap_list in self.heaps.items()
        }
        cloned.heaps = heaps
        cloned.type = self.type
        return cloned

    def visualize(self):
        visualize_heap_manager(self)

class UnionFind:
    def __init__(self, values, type):
        self.parent = list(range(len(values)))
        self.rank = [0] * len(values)
        self.heap_manager = HeapManager(values, type)

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]

    def union(self, x, y):
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x != root_y:
            if self.rank[root_x] > self.rank[root_y]:
                self.parent[root_y] = root_x
                self.heap_manager.merge_heaps(root_x, root_y)
            elif self.rank[root_x] < self.rank[root_y]:
                self.parent[root_x] = root_y
                self.heap_manager.merge_heaps(root_y, root_x)
            else:
                self.parent[root_y] = root_x
                self.rank[root_x] += 1
                self.heap_manager.merge_heaps(root_x, root_y)

    def get_min(self, x):
        root_x = self.find(x)
        return self.heap_manager.get_min(root_x)  # Returns the index

    def get_groups(self):
        groups = {}
        for node in range(len(self.parent)):
            rep = self.find(node)
            if rep not in groups:
                groups[rep] = []
            groups[rep].append(node)
        return groups

    def get_single_representative(self):
        return {x: self.find(x) for x in range(len(self.parent))}

    def duplicate(self):
        cloned = copy(self)
        cloned.parent       = self.parent.copy()
        cloned.rank         = self.rank.copy()
        cloned.heap_manager = self.heap_manager.duplicate()
        return cloned

    def visualize(self):
        visualize_union_find(self)
