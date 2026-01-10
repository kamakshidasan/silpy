import heapq
from silpy.heap.heap import HeapElement
from copy import deepcopy
import numpy as np

# amazing, this is the global simplification procedure that i wrote long back

class FieldOrderer:
    @staticmethod
    def compute_extremum_order(field, extremum_points, field_name, is_maximum):
        field = deepcopy(field)

        queue = []
        visited_order = []
        enqueued_points, visited_points = set(), set()
        invert = is_maximum

        # use the travelling indices
        # build a dictionary that maps index values to their positions
        silpy_index_array = field.mesh.point_data["index"]
        silpy_index_map = {value: position for position, value in enumerate(silpy_index_array)}

        def enqueue_point(point):
            heap_element = HeapElement(point.index, point.scalar, invert)
            heapq.heappush(queue, (heap_element, point))
            enqueued_points.add(point)

        for point in extremum_points:
            enqueue_point(point)

        order_array = np.zeros(field.mesh.n_points, dtype=float)
        running_scalar = np.inf if invert else -np.inf
        running_order = np.float64(field.mesh.n_points - 1) if invert else np.float64(0)

        while queue:
            heap_element, current_point = heapq.heappop(queue)
            enqueued_points.remove(current_point)
            visited_points.add(current_point)

            point_index, point_scalar = current_point.index, current_point.scalar
            running_scalar = (min if invert else max)(running_scalar, point_scalar)

            # Adhitya: new addition here
            position_index = silpy_index_map[point_index]
            order_array[position_index] = running_order
            running_order += -1.0 if invert else 1.0

            for point in current_point.point_neighbors:
                if point not in visited_points and point not in enqueued_points:
                    enqueue_point(point)

        # the one with lowest/highest order becomes -/+ infinity
        field.mesh.point_data['order'] = np.zeros(field.mesh.n_points, dtype=float)
        field.mesh.point_data['order'][:] = order_array

        return field

    @staticmethod
    def compute_minimum_field(field, minimum_points, field_name='order'):
        # all minimum points should be included
        return FieldOrderer.compute_extremum_order(field, minimum_points, field_name, False)

    @staticmethod
    def compute_maximum_field(field, maximum_points, field_name='order'):
        # all maximum points should be included
        return FieldOrderer.compute_extremum_order(field, maximum_points, field_name, True)
