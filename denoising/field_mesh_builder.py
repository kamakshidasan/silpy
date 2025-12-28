import numpy as np
import pyvista as pv

class FieldMeshBuilder3D:
    def __init__(self, mesh, patch_indices):
        self.mesh = mesh
        self.patch_indices = patch_indices
        self.persistent_key = "silpyIndex"

        # cut out the field patch using the indices
        # we need this entire class because of one small thing:
        # when you have segmentation of extremum-saddle in 3D,
        # it gives you all the points
        # but these points can be connected by triangles and lines also
        # and not just tetrahedra

        # so this class does that arduous job of
        # a) finding all tetrahedra associated with the points
        # b) finding all triangles associated with the points
        # c) finding all edges associated with the points
        # d) merging the above subgrids together
        # e) cleaning any arrays created by PyVista during the process

        self.patch_mesh = self.build_patch_mesh()

    def build_edges_polydata(self):
        edges_polydata = self.mesh.extract_all_edges()
        return edges_polydata

    def build_triangles_polydata(self):
        tetra_cell_array = self.mesh.cells.reshape(-1, 5)
        tetra_point_ids = tetra_cell_array[:, 1:]
        tetra_count = tetra_point_ids.shape[0]

        triangle_triplets = np.concatenate([
            tetra_point_ids[:, [0, 1, 2]],
            tetra_point_ids[:, [0, 1, 3]],
            tetra_point_ids[:, [0, 2, 3]],
            tetra_point_ids[:, [1, 2, 3]],
        ], axis=0)

        triangle_triplets_sorted = np.sort(triangle_triplets, axis=1)
        unique_sorted, unique_first_indices = np.unique(
            triangle_triplets_sorted, axis=0, return_index=True
        )

        triangle_triplets_unique_oriented = triangle_triplets[unique_first_indices]

        triangle_face_sizes = np.full((triangle_triplets_unique_oriented.shape[0], 1), 3, dtype=np.int64)
        triangle_faces_stream = np.hstack([triangle_face_sizes, triangle_triplets_unique_oriented]).ravel()

        triangles_polydata = pv.PolyData(self.mesh.points, triangle_faces_stream)

        for array_name in self.mesh.point_data.keys():
            triangles_polydata.point_data[array_name] = self.mesh.point_data[array_name]
        for array_name in self.mesh.field_data.keys():
            triangles_polydata.field_data[array_name] = self.mesh.field_data[array_name]

        return triangles_polydata

    def build_tetrahedra_grid(self):
        tetrahedra_grid = self.mesh.copy(deep=True)
        return tetrahedra_grid

    def build_selected_subgrids(self, edges_polydata, triangles_polydata, tetrahedra_grid):
        selected_patch_indices = np.array(list(self.patch_indices), dtype=int)

        edges_point_mask = np.isin(
            edges_polydata.point_data[self.persistent_key],
            selected_patch_indices,
            assume_unique=True
        )
        edges_subgrid = edges_polydata.extract_points(
            ind=edges_point_mask,
            adjacent_cells=False,
            include_cells=True
        )

        triangles_point_mask = np.isin(
            triangles_polydata.point_data[self.persistent_key],
            selected_patch_indices,
            assume_unique=True
        )
        triangles_subgrid = triangles_polydata.extract_points(
            ind=triangles_point_mask,
            adjacent_cells=False,
            include_cells=True
        )

        tetrahedra_point_mask = np.isin(
            tetrahedra_grid.point_data[self.persistent_key],
            selected_patch_indices,
            assume_unique=True
        )
        tetrahedra_subgrid = tetrahedra_grid.extract_points(
            ind=tetrahedra_point_mask,
            adjacent_cells=False,
            include_cells=True
        )

        return edges_subgrid, triangles_subgrid, tetrahedra_subgrid

    def build_merged_grid(self, tetrahedra_subgrid, triangles_subgrid, edges_subgrid):
        datasets_in_merge_order = [tetrahedra_subgrid, triangles_subgrid, edges_subgrid]

        merged_grid = pv.merge(
            datasets_in_merge_order,
            merge_points=True
        )

        merged_grid = merged_grid.clean()
        return merged_grid

    def whitelist_original_arrays(self, merged_grid):
        original_point_array_names = list(self.mesh.point_data.keys())
        original_cell_array_names = list(self.mesh.cell_data.keys())
        original_field_array_names = list(self.mesh.field_data.keys())

        for data_container, whitelist in [
            (merged_grid.point_data, original_point_array_names),
            (merged_grid.cell_data,  original_cell_array_names),
            (merged_grid.field_data, original_field_array_names),
        ]:
            for array_name in list(data_container.keys()):
                if array_name not in whitelist:
                    del data_container[array_name]

        return merged_grid

    def build_patch_mesh(self):
        edges_polydata = self.build_edges_polydata()
        triangles_polydata = self.build_triangles_polydata()
        tetrahedra_grid = self.build_tetrahedra_grid()

        edges_subgrid, triangles_subgrid, tetrahedra_subgrid = self.build_selected_subgrids(
            edges_polydata=edges_polydata,
            triangles_polydata=triangles_polydata,
            tetrahedra_grid=tetrahedra_grid
        )

        merged_grid = self.build_merged_grid(
            tetrahedra_subgrid=tetrahedra_subgrid,
            triangles_subgrid=triangles_subgrid,
            edges_subgrid=edges_subgrid
        )

        merged_grid = self.whitelist_original_arrays(merged_grid=merged_grid)
        return merged_grid
