# field_builder_3d.py
import numpy as np
import pyvista as pv

class FieldBuilder3D:
    @staticmethod
    def create_structured_grid(volume_matrix, field_name="gaussian", spacing=(1.0, 1.0, 1.0), origin=(0.0, 0.0, 0.0)):
        height, width, depth = volume_matrix.shape
        index_y, index_x, index_z = np.mgrid[0:height, 0:width, 0:depth]

        x_coordinates_3d = index_x.astype(np.float32) * spacing[0] + origin[0]
        y_coordinates_3d = index_y.astype(np.float32) * spacing[1] + origin[1]
        z_coordinates_3d = index_z.astype(np.float32) * spacing[2] + origin[2]

        structured_grid = pv.StructuredGrid(x_coordinates_3d, y_coordinates_3d, z_coordinates_3d)
        structured_grid.point_data[field_name] = volume_matrix.ravel(order="F")
        return structured_grid

    @staticmethod
    def tetrahedralize_structured_grid(structured_grid, field_name="gaussian"):

        number_x, number_y, number_z = structured_grid.dimensions
        cell_count_x, cell_count_y, cell_count_z = number_x - 1, number_y - 1, number_z - 1

        stride_x = 1
        stride_y = number_x
        stride_z = number_x * number_y

        index_x = np.arange(cell_count_x, dtype=np.int64)[:, None, None]
        index_y = np.arange(cell_count_y, dtype=np.int64)[None, :, None]
        index_z = np.arange(cell_count_z, dtype=np.int64)[None, None, :]

        linear_index_base = index_x + index_y * number_x + index_z * number_x * number_y

        point_index_000 = linear_index_base
        point_index_100 = linear_index_base + stride_x
        point_index_010 = linear_index_base + stride_y
        point_index_110 = linear_index_base + stride_y + stride_x
        point_index_001 = linear_index_base + stride_z
        point_index_101 = linear_index_base + stride_z + stride_x
        point_index_011 = linear_index_base + stride_z + stride_y
        point_index_111 = linear_index_base + stride_z + stride_y + stride_x

        flattened_index_000 = point_index_000.ravel()
        flattened_index_100 = point_index_100.ravel()
        flattened_index_010 = point_index_010.ravel()
        flattened_index_110 = point_index_110.ravel()
        flattened_index_001 = point_index_001.ravel()
        flattened_index_101 = point_index_101.ravel()
        flattened_index_011 = point_index_011.ravel()
        flattened_index_111 = point_index_111.ravel()

        number_of_cells = linear_index_base.size
        number_of_tetrahedra = number_of_cells * 6

        tetrahedra_array = np.empty((number_of_tetrahedra, 4), dtype=np.int64)

        block_start = 0
        block_end = number_of_cells
        tetrahedra_array[block_start:block_end, 0] = flattened_index_000
        tetrahedra_array[block_start:block_end, 1] = flattened_index_100
        tetrahedra_array[block_start:block_end, 2] = flattened_index_110
        tetrahedra_array[block_start:block_end, 3] = flattened_index_111

        block_start = block_end
        block_end += number_of_cells
        tetrahedra_array[block_start:block_end, 0] = flattened_index_000
        tetrahedra_array[block_start:block_end, 1] = flattened_index_110
        tetrahedra_array[block_start:block_end, 2] = flattened_index_010
        tetrahedra_array[block_start:block_end, 3] = flattened_index_111

        block_start = block_end
        block_end += number_of_cells
        tetrahedra_array[block_start:block_end, 0] = flattened_index_000
        tetrahedra_array[block_start:block_end, 1] = flattened_index_010
        tetrahedra_array[block_start:block_end, 2] = flattened_index_011
        tetrahedra_array[block_start:block_end, 3] = flattened_index_111

        block_start = block_end
        block_end += number_of_cells
        tetrahedra_array[block_start:block_end, 0] = flattened_index_000
        tetrahedra_array[block_start:block_end, 1] = flattened_index_011
        tetrahedra_array[block_start:block_end, 2] = flattened_index_001
        tetrahedra_array[block_start:block_end, 3] = flattened_index_111

        block_start = block_end
        block_end += number_of_cells
        tetrahedra_array[block_start:block_end, 0] = flattened_index_000
        tetrahedra_array[block_start:block_end, 1] = flattened_index_001
        tetrahedra_array[block_start:block_end, 2] = flattened_index_101
        tetrahedra_array[block_start:block_end, 3] = flattened_index_111

        block_start = block_end
        block_end += number_of_cells
        tetrahedra_array[block_start:block_end, 0] = flattened_index_000
        tetrahedra_array[block_start:block_end, 1] = flattened_index_101
        tetrahedra_array[block_start:block_end, 2] = flattened_index_100
        tetrahedra_array[block_start:block_end, 3] = flattened_index_111

        connectivity_with_sizes = np.empty(number_of_tetrahedra * 5, dtype=np.int64)
        connectivity_with_sizes[0::5] = 4
        connectivity_with_sizes[1::5] = tetrahedra_array[:, 0]
        connectivity_with_sizes[2::5] = tetrahedra_array[:, 1]
        connectivity_with_sizes[3::5] = tetrahedra_array[:, 2]
        connectivity_with_sizes[4::5] = tetrahedra_array[:, 3]

        cell_types_array = np.empty(number_of_tetrahedra, dtype=np.uint8)
        cell_types_array[:] = pv.CellType.TETRA
        points_array = structured_grid.points

        tetrahedral_mesh = pv.UnstructuredGrid(connectivity_with_sizes, cell_types_array, points_array)
        tetrahedral_mesh.point_data[field_name] = structured_grid.point_data[field_name]

        return tetrahedral_mesh
