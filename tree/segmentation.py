from collections import defaultdict, deque
import heapq
import multiprocessing
import os
import time


_POINTS_BY_INDEX = None


def _debug_print(message):
    if not Segmentation.debug_enabled:
        return
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp} pid={os.getpid()}] {message}", flush=True)


def _count_internal_nodes_not_ready(remaining_children_by_node_index):
    not_ready_count = 0
    for remaining_children in remaining_children_by_node_index.values():
        if remaining_children > 0:
            not_ready_count += 1
    return not_ready_count


def _compute_tree_arc_segmentation_task(start_index, end_index, seed_set_for_start, visited_indices=None):
    start_point = _POINTS_BY_INDEX[start_index]
    end_point = _POINTS_BY_INDEX[end_index]

    if visited_indices is None:
        visited_indices = set()
    else:
        visited_indices = set(visited_indices)

    initial_seed_indices = []
    for seed_index in seed_set_for_start:
        if seed_index not in visited_indices:
            initial_seed_indices.append(seed_index)

    queue = deque([start_index] + initial_seed_indices)

    tracked = set(queue)
    tracked.update(visited_indices)

    path_indices = []
    reassigned_indices = []

    ascending = start_point < end_point
    descending = start_point > end_point

    while queue:
        point_index = queue.popleft()
        point = _POINTS_BY_INDEX[point_index]

        within_ascending = start_point <= point < end_point
        within_descending = start_point >= point > end_point

        if (ascending and within_ascending) or (descending and within_descending):
            path_indices.append(point_index)
            for neighbor in point.point_neighbors:
                neighbor_index = neighbor.index
                if neighbor_index not in tracked:
                    tracked.add(neighbor_index)
                    queue.append(neighbor_index)
        else:
            reassigned_indices.append(point_index)

    path_indices = list(set(path_indices))
    reassigned_indices = list(set(reassigned_indices))

    return start_index, end_index, path_indices, reassigned_indices, len(initial_seed_indices)


class Segmentation:
    debug_enabled = False
    debug_verbose = False
    max_processes = None

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
        global _POINTS_BY_INDEX

        arcs = {}

        leaves = tree.get_leaves()
        internal_nodes = tree.get_internal_nodes()
        roots = tree.get_roots()

        root = roots[0]
        root_saddle = tree.get_children(root)[0]

        points_by_index = {}
        for point in tree.manager.points.values():
            points_by_index[point.index] = point

        _POINTS_BY_INDEX = points_by_index

        leaf_indices = [node.index for node in leaves]
        internal_indices = [node.index for node in internal_nodes]
        root_index = root.index
        root_saddle_index = root_saddle.index

        _debug_print(
            f"Setup: leaves={len(leaf_indices)} internal={len(internal_indices)} "
            f"total_points={len(points_by_index)} root={root_index} root_saddle={root_saddle_index}"
        )

        multiprocessing_context = multiprocessing.get_context("fork")

        seeds_by_node_index = defaultdict(set)

        remaining_children_by_node_index = {}
        for node in internal_nodes:
            if node.index == root_saddle_index:
                continue
            if node.index == root_index:
                continue
            remaining_children_by_node_index[node.index] = len(tree.get_children(node))

        _debug_print(f"Counters created for internal nodes: {len(remaining_children_by_node_index)}")

        parent_index_by_node_index = {}
        for node in leaves:
            parent_index_by_node_index[node.index] = tree.get_parents(node)[0].index
        for node in internal_nodes:
            if node.index == root_saddle_index:
                continue
            if node.index == root_index:
                continue
            parent_index_by_node_index[node.index] = tree.get_parents(node)[0].index

        expected_results = len(leaf_indices) + len(internal_indices) - 1
        _debug_print(f"Scheduled arcs (results expected): {expected_results}")

        completed_indices = set()
        completed_results = 0
        progress_step = max(1, expected_results // 20)

        results_queue = multiprocessing_context.Queue()

        def _on_done(result_tuple):
            results_queue.put(("ok", result_tuple))

        def _on_error(exception):
            results_queue.put(("error", repr(exception)))

        process_count = multiprocessing_context.cpu_count()
        if Segmentation.max_processes is not None:
            process_count = min(process_count, Segmentation.max_processes)
        process_count = max(1, process_count)

        _debug_print(f"Starting worker processes: {process_count}")

        pool = multiprocessing_context.Pool(processes=process_count)

        def _submit_arc(start_node_index):
            end_node_index = parent_index_by_node_index[start_node_index]
            seed_set_for_start = seeds_by_node_index[start_node_index]

            visited_indices = None

            pool.apply_async(
                _compute_tree_arc_segmentation_task,
                args=(start_node_index, end_node_index, seed_set_for_start, visited_indices),
                callback=_on_done,
                error_callback=_on_error,
            )

            if Segmentation.debug_enabled and Segmentation.debug_verbose:
                _debug_print(
                    f"Submitted arc start={start_node_index} end={end_node_index} "
                    f"seed_size={len(seed_set_for_start)} visited_size={(0 if visited_indices is None else len(visited_indices))}"
                )

        for leaf_index in leaf_indices:
            _submit_arc(leaf_index)

        _debug_print(f"Enqueued initial leaves: {len(leaf_indices)}")

        while completed_results < expected_results:
            status, payload = results_queue.get()

            if status == "error":
                pool.terminate()
                pool.join()
                raise RuntimeError(f"Worker error: {payload}")

            start_index, end_index, arc_point_indices, reassigned_indices, initial_seed_count = payload

            start_node = points_by_index[start_index]
            end_node = points_by_index[end_index]
            arc_key = Segmentation.make_arc_key(tree, start_node, end_node)

            arcs[arc_key] = [points_by_index[point_index] for point_index in arc_point_indices]
            completed_indices.update(arc_point_indices)

            if reassigned_indices:
                seeds_by_node_index[end_index].update(reassigned_indices)

            completed_results += 1

            if end_index in remaining_children_by_node_index:
                remaining_children_by_node_index[end_index] -= 1
                if remaining_children_by_node_index[end_index] == 0:
                    _submit_arc(end_index)

            if Segmentation.debug_enabled:
                if completed_results % progress_step == 0 or completed_results == expected_results:
                    remaining_results = expected_results - completed_results
                    internal_not_ready = _count_internal_nodes_not_ready(remaining_children_by_node_index)
                    sample = arc_point_indices[:5]
                    _debug_print(
                        f"Collected {completed_results}/{expected_results} results "
                        f"(remaining_results={remaining_results}). "
                        f"internal_not_ready={internal_not_ready}. "
                        f"Last arc start={start_index} end={end_index} "
                        f"path_len={len(arc_point_indices)} reassigned={len(reassigned_indices)} initial_seeds={initial_seed_count} "
                        f"seed_end_size={len(seeds_by_node_index[end_index])} "
                        f"sample_points={sample}"
                    )

        pool.close()
        pool.join()

        _debug_print("All workers joined. Building root arc segmentation.")

        all_indices = set(points_by_index.keys())
        remaining_indices = all_indices - completed_indices

        remaining_seed_indices = seeds_by_node_index[root_saddle_index] & remaining_indices

        last_arc_indices = set().union(
            {root_saddle_index},
            remaining_seed_indices,
            remaining_indices,
            {root_index},
        )

        _debug_print(
            f"Root arc: remaining_points={len(remaining_indices)} "
            f"remaining_seeds_at_root_saddle={len(remaining_seed_indices)} "
            f"last_arc_size={len(last_arc_indices)}"
        )

        arc_key = Segmentation.make_arc_key(tree, root_saddle, root)
        arcs[arc_key] = [points_by_index[point_index] for point_index in last_arc_indices]

        return arcs
