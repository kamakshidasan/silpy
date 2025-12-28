import numpy as np
from .point_types import REGULAR, MAXIMUM, MINIMUM, BOTH, SPLIT, JOIN


class CornerAnalyzer:
    # Neighbor slot order: (up, right, bottom_right, down, left, top_left) -> (0, 1, 2, 3, 4, 5)
    #
    # IMPORTANT: lookup index is always built with:
    # center_lookup_index |= (1 << bit_index)
    # so bit0 corresponds to neighbor_slots[0], bit1 to neighbor_slots[1], etc.

    BOTTOM_LEFT_LOOKUP = np.array([MAXIMUM, REGULAR, REGULAR, MINIMUM], dtype=np.uint8)
    BOTTOM_RIGHT_LOOKUP = np.array([MAXIMUM, REGULAR, REGULAR, SPLIT, JOIN, REGULAR, REGULAR, MINIMUM], dtype=np.uint8)
    TOP_LEFT_LOOKUP = np.array([MAXIMUM, REGULAR, JOIN, REGULAR, REGULAR, SPLIT, REGULAR, MINIMUM], dtype=np.uint8)
    TOP_RIGHT_LOOKUP = np.array([MAXIMUM, REGULAR, REGULAR, MINIMUM], dtype=np.uint8)

    # corner_row: 0 -> bottom row, -1 -> top row
    # corner_col: 0 -> left col, -1 -> right col
    # neighbor_slots: slot indices in the exact lookup bit order
    # neighbor_mask: the 6-slot existence mask stored into neighbor_masks for this corner
    CORNER_SPECS = {
        "bottom_left": (0, 0, (0, 1), 0b000011, BOTTOM_LEFT_LOOKUP),         # up, right
        "bottom_right": (0, -1, (0, 4, 5), 0b110001, BOTTOM_RIGHT_LOOKUP),   # up, left, top_left
        "top_left": (-1, 0, (1, 2, 3), 0b001110, TOP_LEFT_LOOKUP),           # right, bottom_right, down
        "top_right": (-1, -1, (3, 4), 0b011000, TOP_RIGHT_LOOKUP),           # down, left
    }

    @staticmethod
    def get_neighbor_indices(center_index, grid_width):
        up_index = center_index + grid_width
        right_index = center_index + 1
        bottom_right_index = center_index - grid_width + 1
        down_index = center_index - grid_width
        left_index = center_index - 1
        top_left_index = center_index + grid_width - 1
        return (up_index, right_index, bottom_right_index, down_index, left_index, top_left_index)

    @staticmethod
    def analyze_corner(scalars, width, height, point_types, critical_flags, link_masks, neighbor_masks, corner_name):
        corner_row, corner_col, neighbor_slots, neighbor_mask, corner_lookup = CornerAnalyzer.CORNER_SPECS[corner_name]

        y_index = (0, height - 1)[corner_row]
        x_index = (0, width - 1)[corner_col]
        center_index = (y_index * width) + x_index

        center_value = scalars[center_index]
        all_neighbors = CornerAnalyzer.get_neighbor_indices(center_index, width)

        center_lookup_index, center_link_mask = 0, 0

        for bit_index, neighbor_slot in enumerate(neighbor_slots):
            neighbor_index = all_neighbors[neighbor_slot]
            neighbor_value = scalars[neighbor_index]
            is_neighbor_higher = neighbor_value > center_value
            is_neighbor_tied = (neighbor_value == center_value) and (neighbor_index > center_index)
            if is_neighbor_higher or is_neighbor_tied:
                center_lookup_index |= (1 << bit_index)
                center_link_mask |= (1 << neighbor_slot)

        point_type = corner_lookup[center_lookup_index]
        point_types[center_index] = point_type
        critical_flags[center_index] = point_type != REGULAR
        link_masks[center_index] = np.uint8(center_link_mask)
        neighbor_masks[center_index] = np.uint8(neighbor_mask)

    @staticmethod
    def analyze_all_corners(scalars, width, height, point_types, critical_flags, link_masks, neighbor_masks):
        for corner_name in CornerAnalyzer.CORNER_SPECS:
            CornerAnalyzer.analyze_corner(scalars, width, height, point_types, critical_flags, link_masks, neighbor_masks, corner_name)
