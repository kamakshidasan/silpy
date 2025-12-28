from numba import njit


def get_neighbor_indices(center_index, grid_width):
    up_index = center_index + grid_width
    right_index = center_index + 1
    bottom_right_index = center_index - grid_width + 1
    down_index = center_index - grid_width
    left_index = center_index - 1
    top_left_index = center_index + grid_width - 1
    return (up_index, right_index, bottom_right_index, down_index, left_index, top_left_index)


@njit
def get_neighbor_indices_numba(center_index, grid_width):
    up_index = center_index + grid_width
    right_index = center_index + 1
    bottom_right_index = center_index - grid_width + 1
    down_index = center_index - grid_width
    left_index = center_index - 1
    top_left_index = center_index + grid_width - 1
    return (up_index, right_index, bottom_right_index, down_index, left_index, top_left_index)
