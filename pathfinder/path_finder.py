from collections import deque
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import sys

_global_points = None
_global_points_set = None
_global_link_key = None
_global_index_key = None


def _process_component_batch_indices(task):
    critical_point_index, component_start_index, component_end_index = task

    critical_point = _global_points[critical_point_index]
    results = []

    component_index = component_start_index
    while component_index < component_end_index:
        component = critical_point[_global_link_key][component_index]
        reached_point = PathFinder._traverse_link_till_target_using_points_set(
            start_points=component,
            source_point=critical_point,
            link_name=_global_link_key,
            points_set=_global_points_set,
        )
        results.append((critical_point[_global_index_key], reached_point[_global_index_key]))
        component_index += 1

    return results


class PathFinder:
    @staticmethod
    def find_all_monotone_paths(points, link_key, index_key, max_workers=None, batch_size=256, chunksize=16):
        # For each critical point, traverse its upper/lower link to every other critical point,
        # returning a sorted list of tuples containing their join/split indices

        if max_workers is None:
            max_workers = max(multiprocessing.cpu_count() - 1, 1)

        can_use_fork = "fork" in multiprocessing.get_all_start_methods()

        if not can_use_fork:
            sorted_paths = []
            points_set = set(points)

            for critical_point in points:
                target_points = points_set - {critical_point}
                for component in critical_point[link_key]:
                    next_point = PathFinder.traverse_link_till_target(component, target_points, link_key)
                    sorted_paths.append((critical_point[index_key], next_point[index_key]))

            return sorted(sorted_paths)

        global _global_points, _global_points_set, _global_link_key, _global_index_key
        _global_points = list(points)
        _global_points_set = set(points)
        _global_link_key = link_key
        _global_index_key = index_key

        multiprocessing_context = multiprocessing.get_context("fork")

        tasks = []
        critical_point_index = 0
        while critical_point_index < len(_global_points):
            critical_point = _global_points[critical_point_index]
            components_count = len(critical_point[link_key])

            component_start_index = 0
            while component_start_index < components_count:
                component_end_index = min(component_start_index + batch_size, components_count)
                tasks.append((critical_point_index, component_start_index, component_end_index))
                component_start_index = component_end_index

            critical_point_index += 1

        sorted_paths = []
        with ProcessPoolExecutor(
            max_workers=max_workers,
            mp_context=multiprocessing_context,
        ) as executor:
            for batch_results in executor.map(_process_component_batch_indices, tasks, chunksize=chunksize):
                sorted_paths.extend(batch_results)

        return sorted(sorted_paths)

    @staticmethod
    def traverse_link_till_target(start_points, target_points, link_name):
        # Perform a breadth-first search from start_points
        # till it hits a point in target_points just using upper/lower link
        targets = set(target_points)
        discovered_points = set(start_points)

        # return any start that's already a target
        # this := is a walrus operator
        if (existing_target := discovered_points & targets):
            return existing_target.pop()

        point_queue = deque(start_points)
        while point_queue:
            current_point = point_queue.popleft()
            # thanks to __getitem__, this returns upper_link or lower_link
            neighbor_components = current_point[link_name]
            for component in neighbor_components:
                for neighbor_point in component:
                    if neighbor_point in targets:
                        return neighbor_point
                    if neighbor_point not in discovered_points:
                        discovered_points.add(neighbor_point)
                        point_queue.append(neighbor_point)

        # run and hide if you ever hit here
        return None

    @staticmethod
    def _traverse_link_till_target_using_points_set(start_points, source_point, link_name, points_set):
        discovered_points = set(start_points)

        for start_point in discovered_points:
            if start_point in points_set and start_point != source_point:
                return start_point

        point_queue = deque(start_points)
        while point_queue:
            current_point = point_queue.popleft()
            neighbor_components = current_point[link_name]
            for component in neighbor_components:
                for neighbor_point in component:
                    if neighbor_point in points_set and neighbor_point != source_point:
                        return neighbor_point
                    if neighbor_point not in discovered_points:
                        discovered_points.add(neighbor_point)
                        point_queue.append(neighbor_point)

        return None
