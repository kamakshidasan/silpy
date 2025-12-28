from copy import deepcopy
import numpy as np
from ..denoising.field_cutter import FieldCutter3D
from ..denoising.finder import Finder3D
from ..field.field import Field
from ..field.field_analyzer import FieldAnalyzer
from ..denoising.field_orderer import FieldOrderer3D

class FieldSimplification3D:
    def __init__(self, field, field_name, tree_type, removable_point):
        self.field = field
        self.field_name = field_name
        self.tree_type = tree_type
        self.removable_point = removable_point

        self.field_cutter = self.initialize_field_cutter(field, field_name, tree_type, removable_point)

        self.finder = Finder3D(self.order_points, self.removable_parent, self.removable_point)

        self.patch_field = Field(mesh=self.patch_infinity_mesh)

        self.patch_field = self.update_patch_field_until_sufficient(self.removable_point, self.finder, self.patch_field)

        self.new_order_field = self.update_order_mesh(self.patch_field, self.order_mesh, self.removable_point, self.removable_parent)

        self.flattened_field = self.flatten_scalars_to_saddle(self.field, self.field_name)

        self.final_field = self.apply_numeric_perturbation_from_order(self.flattened_field, self.new_order_field, self.field_name, make_increasing=True)


    def initialize_field_cutter(self, field, field_name, tree_type, removable_point):
        field_cutter = FieldCutter3D(field, field_name, tree_type, removable_point)
        self.field_cutter = field_cutter
        self.removable_parent = field_cutter.extremum_parent
        self.order_points = field_cutter.order_points
        self.patch_infinity_mesh = field_cutter.patch_infinity_mesh
        self.order_mesh = field_cutter.mesh

        # self.order_field = Field(mesh=self.order_mesh)
        # finder.visualize(self.order_field, 'order')
        #
        # self.patch_mesh_before_infinity = field_cutter.patch_mesh
        # self.patch_field_before_infinity = Field(mesh=self.patch_mesh_before_infinity)
        # self.patch_points_before_infinity = FieldAnalyzer(self.patch_field_before_infinity, 'order').points
        # self.patch_scalars_before_infinity = sorted([point.scalar for point in self.patch_points_before_infinity.values()], reverse=True)



        return field_cutter

    def update_patch_field_until_sufficient(self, removable_point, finder, patch_field, max_iterations=50):
        if removable_point.type == 'minimum':
            find_legal_extremum = finder.find_legal_minimum
            construct_field_from_extremum = FieldOrderer3D.compute_minimum_field
            find_complementary_extremums = finder.find_legal_maximums
            construct_field_from_complementary_extremums = FieldOrderer3D.compute_maximum_field

        elif removable_point.type == 'maximum':
            find_legal_extremum = finder.find_legal_maximum
            construct_field_from_extremum = FieldOrderer3D.compute_maximum_field
            find_complementary_extremums = finder.find_legal_minimums
            construct_field_from_complementary_extremums = FieldOrderer3D.compute_minimum_field

        if removable_point.type in ('minimum', 'maximum'):
            count = 0

            # iterate by alternating included-maximum and included-minimum updates
            while count < max_iterations:

                #print("sufficient count: ", count)
                count += 1

                # check whether the current field already meets the sufficiency criterion
                is_patch_field_sufficient = finder.is_field_sufficient(patch_field)
                if is_patch_field_sufficient:
                    break

                # find the single legal maximum on the current field and include it
                extremum_point = find_legal_extremum(patch_field)
                extremum_field = construct_field_from_extremum(patch_field, [extremum_point])

                # if the maximum-tightened field is sufficient, adopt it and say bye
                is_extremum_field_sufficient = finder.is_field_sufficient(extremum_field)
                if is_extremum_field_sufficient:
                    patch_field = extremum_field
                    break

                # otherwise tighten via minimum inclusion:
                # find all legal minimums on the maximum-tightened field and include them.
                complementary_extremum_points = find_complementary_extremums(extremum_field)
                complementary_extremum_field = construct_field_from_complementary_extremums(extremum_field, complementary_extremum_points)

                # promote the minimum-tightened field and continue the loop
                patch_field = complementary_extremum_field

        return patch_field

    def update_order_mesh(self, patch_field, order_mesh, removable_point, removable_parent):
        # our order is between 0 and the number of points
        # that should be changed to the orders we removed

        local_orders_on_patch = patch_field.mesh.point_data['order']
        global_indices_on_patch = patch_field.mesh.point_data['silpyIndex'].astype(int)

        saddle_global_index = int(removable_parent.index)

        current_global_order_values = order_mesh.point_data['order'].astype(np.int64)
        number_of_vertices = current_global_order_values.shape[0]

        # 1) Primary key after flatten: set every vertex in the segment to the saddle's global order
        flattened_primary_order_values = current_global_order_values.copy()
        saddle_primary_key = current_global_order_values[saddle_global_index]
        flattened_primary_order_values[global_indices_on_patch] = saddle_primary_key

        # 2) Secondary key: local order inside the segment; zero elsewhere.
        #    Force the saddle to be the largest inside its bucket so it ends last.
        secondary_local_order_values = np.zeros(number_of_vertices, dtype=np.int64)
        secondary_local_order_values[global_indices_on_patch] = local_orders_on_patch.astype(np.int64)
        secondary_local_order_values[saddle_global_index] = np.iinfo(np.int64).max

        # 3) Tertiary deterministic key: vertex id (global index)
        tertiary_vertex_indices = np.arange(number_of_vertices, dtype=np.int64)

        # 4) Global stable recompute: sort by (primary, secondary, tertiary)
        #    np.lexsort uses last key as primary, so pass (tertiary, secondary, primary)
        sorted_global_indices = np.lexsort((tertiary_vertex_indices, secondary_local_order_values, flattened_primary_order_values))

        # 5) Write back ranks as the new order
        new_order_mesh = deepcopy(order_mesh)
        updated_order_values = new_order_mesh.point_data['order'].copy()
        updated_order_values[sorted_global_indices] = np.arange(number_of_vertices, dtype=updated_order_values.dtype)
        new_order_mesh.point_data['order'] = updated_order_values

        order_field = Field(mesh=new_order_mesh)
        return order_field


    def flatten_scalars_to_saddle(self, original_field, array_name):
        segment_global_indices = self.patch_field.mesh.point_data['silpyIndex'].astype(int)
        saddle_global_index = int(self.removable_parent.index)

        updated_mesh = deepcopy(original_field.mesh)
        updated_scalar_values = updated_mesh.point_data[array_name].astype(np.float64, copy=True)

        saddle_value = float(updated_scalar_values[saddle_global_index])
        updated_scalar_values[np.asarray(segment_global_indices, dtype=int)] = saddle_value

        updated_mesh.point_data[array_name] = updated_scalar_values
        return Field(mesh=updated_mesh)


    def apply_numeric_perturbation_from_order(self, original_field, order_field, array_name='gaussian', make_increasing=True):

        order_values = order_field.mesh.point_data['order']
        indices_in_order = np.argsort(order_values)

        updated_mesh = deepcopy(original_field.mesh)
        values = updated_mesh.point_data[array_name].astype(np.float64, copy=True)

        if make_increasing:
            for position_in_traversal in range(1, len(indices_in_order)):
                previous_index = indices_in_order[position_in_traversal - 1]
                current_index = indices_in_order[position_in_traversal]
                if values[current_index] <= values[previous_index]:
                    values[current_index] = np.nextafter(values[previous_index], np.inf)
        else:
            for position_in_traversal in range(len(indices_in_order) - 1, 0, -1):
                later_index = indices_in_order[position_in_traversal]
                earlier_index = indices_in_order[position_in_traversal - 1]
                if values[earlier_index] <= values[later_index]:
                    values[earlier_index] = np.nextafter(values[later_index], np.inf)

        updated_mesh.point_data[array_name] = values
        return Field(mesh=updated_mesh)
