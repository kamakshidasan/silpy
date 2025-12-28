import numpy as np
from numba import njit, prange
from .point_types import REGULAR, MAXIMUM, MINIMUM, BOTH, SPLIT, JOIN
from .neighbor_indices import get_neighbor_indices_numba


SIX_BIT_MASK = 0b111111


@njit
def compute_upper_runs(mask_value):
    rotated_mask = ((mask_value << 1) & SIX_BIT_MASK) | (mask_value >> 5)
    run_start_mask = mask_value & (~rotated_mask) & SIX_BIT_MASK

    num_set_bits = 0
    for shift_index in range(6):
        num_set_bits += (run_start_mask >> shift_index) & 1

    return num_set_bits


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


@njit(cache=True, parallel=True)
def analyze_all_points_numba(scalars, width, height, point_types, critical_flags, link_masks, neighbor_masks):
    interior_width = width - 2
    interior_height = height - 2
    total_interior_points = interior_width * interior_height

    for linear_index in prange(total_interior_points):
        y_index = (linear_index // interior_width) + 1
        x_index = (linear_index % interior_width) + 1

        center_index = (y_index * width) + x_index
        center_value = scalars[center_index]

        neighbor_indices = get_neighbor_indices_numba(center_index, width)

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
