from ..tree.segmentation import Segmentation
from ..denoising.field_transformer import FieldTransformer3D
from ..denoising.field_tree_builder import FieldTreeBuilder3D
from ..denoising.field_mesh_builder import FieldMeshBuilder3D
from collections import defaultdict
import numpy as np
from copy import deepcopy

class FieldCutter3D:
    def __init__(self, field, field_name, tree_type, removable_point):
        # cut out the order field patch of an extremum point using a reeb tree

        # There are five steps:
        # a) find the order field using the current scalar field
        # b) on that order field find the associated tree: split/join/contour
        # c) for that extremum point that has to be removed,
        # figure out what what is the associated saddle parent
        # d) find out the segmentation associated with the parent - node
        # e) cut out that segmentation and create it into a new mesh
        # along with the travelling indices
        # ** just be careful, this only works for surface meshes for now**

        self.removable_point = removable_point
        self.tree_type = tree_type

        self.setup_order_field(field, field_name)
        self.find_patch_indices()
        self.create_patch_mesh()
        self.create_infinity_patch()


    def setup_order_field(self, field, field_name):
        # create an order field on the existing scalar field
        # don't worry old data wont be changed
        self.order_field = FieldTransformer3D.create_order_field(field, field_name)

        field_builder = FieldTreeBuilder3D(self.order_field, field_name, self.tree_type)

        # get field structures
        self.order_field_data = field_builder.field_data
        self.order_points = field_builder.points
        self.order_critical_points = field_builder.critical_points
        self.order_critical_manager = field_builder.critical_manager
        self.order_tree = field_builder.tree

        # save the mesh - this has order field and indices arrays defined on it
        self.mesh = self.order_field.mesh


    def find_patch_indices(self):

        # the extremum point that we received is from a different field
        # hence the order tree will not have this point object
        # the order tree however will have a point with the same index
        # so find that point corresponding point
        # that will be point you want to remove

        # find the index of the node
        removable_index = self.removable_point.index

        # the point is an extremum, so has to be there in leaves or roots
        candidate_nodes = self.order_tree.get_leaves() + self.order_tree.get_roots()

        # find the node in the tree corresponding to the removable point
        extremum_node = [node for node in candidate_nodes if node.index == removable_index][0]

        # store the point for eternity
        self.extremum_point = extremum_node

        # find the parent of the node in the tree - there will be a parent
        self.extremum_parent = self.order_tree.get_parents(self.extremum_point)[0]

        # find all the points in the segmentation
        arc = Segmentation.find_tree_arc_segmentation(self.extremum_point, self.extremum_parent, defaultdict(list))

        # just dump them all onto a set with the indices
        arc_indices = {point.index for point in arc}

        # the parent will always be a saddle - and may not be included in the segmentation
        arc_indices.add(self.extremum_parent.index)

        # make it globally available
        self.patch_indices = arc_indices

    def create_patch_mesh(self):
        mesh_builder = FieldMeshBuilder3D(self.mesh, self.patch_indices)
        self.patch_mesh = mesh_builder.patch_mesh

    # the extremum parent would be marked as -/+ infinity based on the order
    def create_infinity_patch(self):

        # create a copy of the mesh
        patch_infinity_mesh = deepcopy(self.patch_mesh)

        # use the travelling indices
        silpy_index_array = patch_infinity_mesh.point_data["silpyIndex"]

        # the one with lowest/highest order becomes -/+ infinity
        # we compute this on the patch that has order, so it would be defined
        order_array = patch_infinity_mesh.point_data["order"]

        # build a dictionary that maps silpyIndex values to their positions
        silpy_index_map = {value: position for position, value in enumerate(silpy_index_array)}

        # store the index of the removable_parent
        removable_parent_index = self.extremum_parent.index

        # look up the parent position directly from the dictionary
        parent_position = silpy_index_map[removable_parent_index]

        if self.extremum_point.type == 'maximum':
            # compute the maximum value in the order array
            max_order = np.max(patch_infinity_mesh.point_data["order"])

            # define "infinity" as one greater than the current maximum order
            # i know the guy said put infinity - but i'm like find the highest and add one to that.
            infinity_order = max_order + 1
        else:
            # compute the minimum value in the order array
            min_order = np.min(patch_infinity_mesh.point_data["order"])

            # go the other way
            infinity_order = min_order - 1


        # update the order array at the parent_position with the new infinity_order
        order_array[parent_position] = infinity_order

        self.removable_parent_index = removable_parent_index
        self.silpy_index_map = silpy_index_map
        self.patch_infinity_mesh = patch_infinity_mesh
