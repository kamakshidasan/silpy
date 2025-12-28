import numpy as np
from numba import njit, prange
from .point_types import REGULAR, MAXIMUM, MINIMUM, BOTH, SPLIT, JOIN


SIX_BIT_MASK = 0b111111


@njit
def popcount_6bit(value):
    count = 0
    for _ in range(6):
        count += value & 1
        value >>= 1
    return count


@njit
def rotate_left_6bit(mask_value):
    return ((mask_value << 1) & SIX_BIT_MASK) | (mask_value >> 5)


@njit
def compute_upper_runs(mask_value):
    rotated_mask = rotate_left_6bit(mask_value)
    run_start_bits = mask_value & (~rotated_mask) & SIX_BIT_MASK
    return popcount_6bit(run_start_bits)


@njit
def classify_interior_mask(mask_value):
    if mask_value == 0:
        return MAXIMUM
    if mask_value == SIX_BIT_MASK:
        return MINIMUM

    upper_runs = compute_upper_runs(mask_value)
    if upper_runs >= 2:
        return BOTH
    return REGULAR


@njit
def get_neighbor_indices(center_index, grid_width):
    up_index = center_index + grid_width
    right_index = center_index + 1
    bottom_right_index = center_index - grid_width + 1
    down_index = center_index - grid_width
    left_index = center_index - 1
    top_left_index = center_index + grid_width - 1
    return (up_index, right_index, bottom_right_index, down_index, left_index, top_left_index)


@njit(parallel=True)
def analyze_all_points_numba(scalars, width, height, point_types, critical_flags, link_masks, neighbor_masks):
    for y_index in prange(1, height - 1):
        for x_index in range(1, width - 1):
            center_index = (y_index * width) + x_index
            center_value = scalars[center_index]

            neighbor_indices = get_neighbor_indices(center_index, width)

            mask_value = 0
            for bit_index, neighbor_index in enumerate(neighbor_indices):
                neighbor_value = scalars[neighbor_index]
                is_neighbor_higher = neighbor_value > center_value
                is_neighbor_tied = (neighbor_value == center_value) and (neighbor_index > center_index)
                if is_neighbor_higher or is_neighbor_tied:
                    mask_value |= (1 << bit_index)

            link_masks[center_index] = np.uint8(mask_value)
            neighbor_masks[center_index] = np.uint8(SIX_BIT_MASK)

            point_type = classify_interior_mask(mask_value)
            point_types[center_index] = point_type
            critical_flags[center_index] = point_type != REGULAR


class InteriorAnalyzer:

    @staticmethod
    def analyze_all_points(scalars, width, height, point_types, critical_flags, link_masks, neighbor_masks):
        analyze_all_points_numba(scalars, width, height, point_types, critical_flags, link_masks, neighbor_masks)
