import numpy as np
from copy import deepcopy
from ..field.field_analyzer import FieldAnalyzer

class FieldTransformer:
    @staticmethod
    def create_order_field(field, source_name='gaussian'):
        # duplicate the field
        order_field = deepcopy(field)

        # sort the points using the source scalar field
        field_analyzer = FieldAnalyzer(order_field, source_name)
        sorted_field_points = field_analyzer.get_sorted_points()

        # now create a numpy array that you can use as a scalar field
        order_array = np.zeros(order_field.mesh.n_points, dtype=float)

        # assign the order to the points
        for point_order, point in enumerate(sorted_field_points):
            point.order = point_order
            order_array[int(point.index)] = float(point.order)

        # attach the numpy array to the field
        order_field.mesh.point_data['order'] = order_array
        return order_field
