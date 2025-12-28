from collections import deque
from collections import defaultdict

class PathFinder:
    # Adhitya: PLEASE PARALLELIZE!
    @staticmethod
    def find_all_monotone_paths(points, link_key, index_key):
        # For each critical point, traverse its upper/lower link to every other critical point,
        # returning a sorted list of tuples containing their join/split indices
        sorted_paths = []
        points_set = set(points)

        for critical_point in points:
            target_points = points_set - {critical_point}
            for component in critical_point[link_key]:
                next_point = PathFinder.traverse_link_till_target(component, target_points, link_key)
                sorted_paths.append((critical_point[index_key], next_point[index_key]))

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
