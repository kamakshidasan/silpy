import numpy as np
from .interior_analyzer import InteriorAnalyzer
from .boundary_analyzer import BoundaryAnalyzer
from .corner_analyzer import CornerAnalyzer
from .point_processor import PointProcessor


class FieldAnalyzer(PointProcessor):
    SIX_BIT_MASK = 0b111111

    def __init__(self, field, name):
        self.mesh = field.mesh
        self.name = name
        self.persistent_key = "silpyIndex"

        self.extract_flat_field()
        self.process_mesh()
        self.build_points()
        self.build_links()

        self.mesh.set_active_scalars(self.name)

    def extract_flat_field(self):
        x_min, x_max, y_min, y_max, z_min, z_max = (int(bound) for bound in self.mesh.bounds)
        self.width, self.height = (x_max - x_min) + 1, (y_max - y_min) + 1

        self.indices = np.arange(self.mesh.n_points, dtype=np.int64)
        self.mesh.point_data[self.persistent_key] = self.indices
        self.scalars = self.mesh.point_data[self.name].astype(np.float32)

    def process_mesh(self):
        num_points = int(self.scalars.size)
        self.point_types = np.zeros(num_points, dtype=np.uint8)
        self.critical_flags = np.zeros(num_points, dtype=np.bool_)
        self.neighbor_masks = np.zeros(num_points, dtype=np.uint8)
        self.link_masks = np.zeros(num_points, dtype=np.uint8)

        InteriorAnalyzer.analyze_all_points(self.scalars, self.width, self.height, self.point_types, self.critical_flags, self.link_masks, self.neighbor_masks)
        BoundaryAnalyzer.analyze_all_edges(self.scalars, self.width, self.height, self.point_types, self.critical_flags, self.link_masks, self.neighbor_masks)
        CornerAnalyzer.analyze_all_corners(self.scalars, self.width, self.height, self.point_types, self.critical_flags, self.link_masks, self.neighbor_masks)
