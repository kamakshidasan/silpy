import networkx as nx
from ..branch.branch_decomposition import MergeBranchDecomposition, ContourBranchDecomposition

class BottleneckDistance:
    def __init__(self, input1, input2):
        self.input1 = input1
        self.input2 = input2
        self.pairs1 = self._extract_pairs(input1)
        self.pairs2 = self._extract_pairs(input2)
        self.compute()

    def compute(self):
        # STEP 1: Gather all candidate thresholds
        thresholds = []

        # 1a. Pairwise infinity-norm distances between points
        for birth1, death1 in self.pairs1:
            for birth2, death2 in self.pairs2:
                thresholds.append(max(abs(birth1 - birth2), abs(death1 - death2)))

        # 1b. Half-life distances (cost to diagonal)
        for birth, death in self.pairs1 + self.pairs2:
            thresholds.append((death - birth) / 2.0)

        sorted_thresholds = sorted(set(thresholds))

        # Binary search for minimal feasible threshold
        low, high = 0, len(sorted_thresholds) - 1
        best_threshold = sorted_thresholds[high]
        best_matching = None

        while low <= high:
            mid = (low + high) // 2
            threshold = sorted_thresholds[mid]
            matching = self.match_for_threshold(threshold)
            if matching is not None:
                best_threshold = threshold
                best_matching = matching
                high = mid - 1
            else:
                low = mid + 1

        # Store results
        self.distance = best_threshold
        self.matching = best_matching

    def match_for_threshold(self, threshold):
        graph = nx.Graph()
        left_nodes, right_nodes = [], []

        # Add nodes and diagonal proxies for diagram1
        for index, (birth, death) in enumerate(self.pairs1):
            current_node = ("first", index)
            graph.add_node(current_node, bipartite=0)
            left_nodes.append(current_node)
            half_life = (death - birth) / 2.0
            if half_life <= threshold:
                proxy_node = ("diagonal_first", index)
                graph.add_node(proxy_node, bipartite=1)
                right_nodes.append(proxy_node)
                graph.add_edge(current_node, proxy_node)

        # Add nodes and diagonal proxies for diagram2
        for index, (birth, death) in enumerate(self.pairs2):
            current_node = ("second", index)
            graph.add_node(current_node, bipartite=1)
            right_nodes.append(current_node)
            half_life = (death - birth) / 2.0
            if half_life <= threshold:
                proxy_node = ("diagonal_second", index)
                graph.add_node(proxy_node, bipartite=0)
                left_nodes.append(proxy_node)
                graph.add_edge(proxy_node, current_node)

        # Connect cross-diagram edges
        for index1, (birth1, death1) in enumerate(self.pairs1):
            for index2, (birth2, death2) in enumerate(self.pairs2):
                distance = max(abs(birth1 - birth2), abs(death1 - death2))
                if distance <= threshold:
                    graph.add_edge(("first", index1), ("second", index2))

        # Compute Hopcroft–Karp matching
        matching = nx.algorithms.bipartite.matching.hopcroft_karp_matching(
            graph, top_nodes=left_nodes
        )
        matched_real_nodes = [node for node in matching if node[0] in ("first", "second")]
        if len(matched_real_nodes) == len(self.pairs1) + len(self.pairs2):
            return matching
        return None

    def print_matching(self):
        def get_label(input_obj, pairs, index):
            if isinstance(input_obj, (MergeBranchDecomposition, ContourBranchDecomposition)):
                item = input_obj.branches.items[index]
                return repr(item)
            return repr(pairs[index])

        matches = []
        for node_key, partner_node in self.matching.items():
            if node_key[0] != "first":
                continue

            idx1 = node_key[1]
            repr1 = get_label(self.input1, self.pairs1, idx1)

            if partner_node[0] == "second":
                idx2 = partner_node[1]
                repr2 = get_label(self.input2, self.pairs2, idx2)
                line = f"{repr1} ↔ {repr2}"
            else:
                line = f"{repr1} ↔ diagonal"

            matches.append((idx1, line))

        for _, line in sorted(matches, key=lambda x: x[0]):
            print(line)

    @staticmethod
    def _extract_pairs(input):
        # Detect BranchDecomposition instances
        if isinstance(input, (MergeBranchDecomposition, ContourBranchDecomposition)):
            items = input.branches.items
            pairs = []
            for item in items:
                birth = item.birth.scalar
                death = item.death.scalar
                pairs.append((birth, death))
        else:
            # Assume iterable of raw (birth, death) pairs
            pairs = input
        return pairs
