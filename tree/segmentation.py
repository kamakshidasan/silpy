from collections import defaultdict, deque
import heapq

class Segmentation:
    @staticmethod
    def make_arc_key(tree, node_a, node_b):
        return (node_a, node_b) if tree.has_edge(node_a, node_b) else (node_b, node_a)

    @staticmethod
    def find_tree_arc_segmentation(start_point, end_point, seed_points, visited=None):
        # Build a monotone path of points from start_point toward end_point,
        # reassigning out-of-range points to seed_points[end_point]
        visited = set() if visited is None else visited
        initial = [point for point in set(seed_points[start_point]) if point not in visited]
        queue = deque([start_point] + initial)
        tracked = set(queue) | visited
        path = []

        ascending = start_point < end_point
        descending = start_point > end_point

        while queue:
            point = queue.popleft()

            within_ascending = start_point <= point < end_point
            within_descending = start_point >= point > end_point

            if (ascending and within_ascending) or (descending and within_descending):
                path.append(point)
                for neighbor in point.point_neighbors:
                    if neighbor not in tracked:
                        tracked.add(neighbor)
                        queue.append(neighbor)
            else:
                seed_points[end_point].append(point)

        path = list(set(path))
        return path

    @staticmethod
    def find_merge_tree_segmentation(tree):
        is_increasing = {'join': True, 'split': False}
        increasing = is_increasing[tree.type]

        arcs = {}
        seeds = defaultdict(list)

        # Collect all start nodes in correct order
        start_nodes = tree.get_leaves() + tree.get_internal_nodes()
        start_nodes = sorted(start_nodes, reverse=not increasing)

        # Build an arc path for each node->parent pair
        for start in start_nodes:
            end = tree.get_parents(start)[0]
            arc_key = Segmentation.make_arc_key(tree, start, end)
            arcs[arc_key] = Segmentation.find_tree_arc_segmentation(start, end, seeds)

        # Handle the root saddle separately
        root = tree.get_roots()[0]
        root_saddle = tree.get_children(root)[0]
        arc_key = Segmentation.make_arc_key(tree, root_saddle, root)
        arcs[arc_key].append(root)

        return arcs
