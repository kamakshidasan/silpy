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


    @staticmethod
    def find_contour_tree_segmentation(original_contour_tree):
        contour_tree = original_contour_tree.duplicate()
        arcs = defaultdict(list)
        visited = set()
        seeds = defaultdict(list)
        remaining_nodes = len(contour_tree.nodes)

        # seed initial queue with leaves and roots

        # Initialize the queue with leaves and roots.
        # In contour trees, the order of traversal "somewhat" influences the segmentation.
        #
        # This is because saddles can act as both leaves and roots depending on when they're visited.
        # This leads to ambiguity in how arcs are assigned, especially in 'X'-shaped configurations
        # where a saddle connects two maxima and minima. For instance, a saddle connected to
        # two minima and two maxima logically belongs to multiple arcs, but this implementation
        # assigns it to just one—based on the traversal state at that moment.
        #
        # Unlike merge trees, contour trees do not guarantee a unique segmentation:
        # a saddle may legitimately (lol) belong to more than one arc. Julien’s paper suggests assigning
        # saddles to the “last” arc (typically the one with the most nodes), but this is a bit
        # arbitrary for my liking.
        #
        # Main takeaway:
        # If you're using these segmentations in deep learning pipelines, especially for training,
        # avoid depending directly on contour tree-based labels. Ambiguous saddles—like the 'X'-shaped
        # case—are assigned to just one of their contour arcs, when in fact they belong to several.

        queue = deque()
        queue.extend((node, 'leaf') for node in contour_tree.get_leaves())
        queue.extend((node, 'root') for node in contour_tree.get_roots())

        while remaining_nodes > 1:
            node, node_type = queue.popleft()

            # choose adjacent node based on type
            if node_type == 'leaf':
                adjacent = contour_tree.get_parents(node)[0]
            else:
                adjacent = contour_tree.get_children(node)[0]

            # record the path between node and its adjacent
            path = Segmentation.find_tree_arc_segmentation(node, adjacent, seeds, visited)
            arc_key = Segmentation.make_arc_key(contour_tree, node, adjacent)
            arcs[arc_key] = path

            # mark all points in the returned path as visited
            visited.update(path)

            # reduce node and examine neighbors
            parents, children = contour_tree.reduce_node(node)
            remaining_nodes -= 1
            node_neighbors = parents + children  # track neighbors after reduction

            # enqueue new leaves and roots
            for neighbor in node_neighbors:
                if contour_tree.is_leaf(neighbor):
                    queue.append((neighbor, 'leaf'))
                elif contour_tree.is_root(neighbor):
                    queue.append((neighbor, 'root'))

        # after loop, last_neighbors holds the final node
        final_node = node_neighbors[0]
        final_arc_key = Segmentation.make_arc_key(contour_tree, final_node, node)
        arcs[final_arc_key].append(final_node)

        return arcs
