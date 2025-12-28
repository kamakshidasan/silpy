import numpy as np
from numba import njit, prange
from .point_types import REGULAR, MAXIMUM, MINIMUM, BOTH, SPLIT, JOIN
from .neighbor_indices import get_neighbor_indices_numba


@njit(cache=True, parallel=True)
def analyze_edge_numba(
    scalars, width, height, point_types, critical_flags, link_masks, neighbor_masks,
    axis, position, neighbor_slots, neighbor_mask, edge_lookup
):
    fixed_index = ((0, height - 1)[position], (0, width - 1)[position])[axis]
    start_index = ((fixed_index * width) + 1, width + fixed_index)[axis]
    edge_offset = (1, width)[axis]
    num_points = (width - 2, height - 2)[axis]

    for edge_index in prange(num_points):
        center_index = start_index + (edge_index * edge_offset)
        center_value = scalars[center_index]
        all_neighbors = get_neighbor_indices_numba(center_index, width)

        center_lookup_index, center_link_mask = 0, 0

        for bit_index in range(4):
            neighbor_slot = neighbor_slots[bit_index]
            neighbor_index = all_neighbors[neighbor_slot]
            neighbor_value = scalars[neighbor_index]
            is_neighbor_higher = neighbor_value > center_value
            is_neighbor_tied = (neighbor_value == center_value) and (neighbor_index > center_index)
            if is_neighbor_higher or is_neighbor_tied:
                center_lookup_index |= (1 << bit_index)
                center_link_mask |= (1 << neighbor_slot)

        point_type = edge_lookup[center_lookup_index]
        point_types[center_index] = point_type
        critical_flags[center_index] = point_type != REGULAR
        link_masks[center_index] = np.uint8(center_link_mask)
        neighbor_masks[center_index] = np.uint8(neighbor_mask)


class BoundaryAnalyzer:

    BOTTOM_EDGE_LOOKUP = np.array([MAXIMUM, JOIN, REGULAR, REGULAR, REGULAR, BOTH, SPLIT, SPLIT, JOIN, JOIN, BOTH, REGULAR, REGULAR, REGULAR, SPLIT, MINIMUM], dtype=np.uint8)
    LEFT_EDGE_LOOKUP = np.array([MAXIMUM, REGULAR, JOIN, REGULAR, JOIN, BOTH, JOIN, REGULAR, REGULAR, SPLIT, BOTH, SPLIT, REGULAR, SPLIT, REGULAR, MINIMUM], dtype=np.uint8)
    TOP_EDGE_LOOKUP = np.array([MAXIMUM, REGULAR, JOIN, REGULAR, JOIN, BOTH, JOIN, REGULAR, REGULAR, SPLIT, BOTH, SPLIT, REGULAR, SPLIT, REGULAR, MINIMUM], dtype=np.uint8)
    RIGHT_EDGE_LOOKUP = np.array([MAXIMUM, REGULAR, REGULAR, SPLIT, JOIN, BOTH, REGULAR, SPLIT, JOIN, REGULAR, BOTH, SPLIT, JOIN, REGULAR, REGULAR, MINIMUM], dtype=np.uint8)

    # Neighbor slot order: (up, right, bottom_right, down, left, top_left) -> bits (0, 1, 2, 3, 4, 5)
    #
    # axis: 0 -> row edge (top/bottom), 1 -> column edge (left/right)
    # position: 0 -> first row/col, -1 -> last row/col
    # neighbor_slots: the 4 slots in the exact local bit order (bit0..bit3) used to build center_lookup_index
    # neighbor_mask: the 6-slot existence mask stored into neighbor_masks for this edge (not corners)
    EDGE_SPECS = {
        "bottom": (0, 0, (0, 1, 4, 5), 0b110011, BOTTOM_EDGE_LOOKUP),   # up, right, left, top_left
        "top": (0, -1, (1, 2, 3, 4), 0b011110, TOP_EDGE_LOOKUP),        # right, bottom_right, down, left
        "left": (1, 0, (0, 1, 2, 3), 0b001111, LEFT_EDGE_LOOKUP),       # up, right, bottom_right, down
        "right": (1, -1, (0, 3, 4, 5), 0b111001, RIGHT_EDGE_LOOKUP),    # up, down, left, top_left
    }

    @staticmethod
    def analyze_edge(scalars, width, height, point_types, critical_flags, link_masks, neighbor_masks, edge_name):
        axis, position, neighbor_slots, neighbor_mask, edge_lookup = BoundaryAnalyzer.EDGE_SPECS[edge_name]
        analyze_edge_numba(
            scalars, width, height, point_types, critical_flags, link_masks, neighbor_masks,
            axis, position, neighbor_slots, neighbor_mask, edge_lookup
        )

    @staticmethod
    def analyze_all_edges(scalars, width, height, point_types, critical_flags, link_masks, neighbor_masks):
        for edge_name in BoundaryAnalyzer.EDGE_SPECS:
            BoundaryAnalyzer.analyze_edge(scalars, width, height, point_types, critical_flags, link_masks, neighbor_masks, edge_name)
