import pyvista as pv
from .gaussian_builder import GaussianBuilder
from .field_builder import FieldBuilder
from ..debug.field import plot_field, plot_warped_field

class Field:
    def __init__(self, mesh=None, filename=None):
        self.mesh = mesh
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        self.mesh = pv.read(filename)

    def save(self, filename):
        self.mesh.save(filename)

    def plot(self, name=None, cmap="viridis", warp=False, warp_scale=5.0):
        first_name, *_ = self.mesh.point_data.keys()
        name = name if name is not None else first_name

        if not warp:
            plot_field(self.mesh, name=name, cmap=cmap)
        else:
            plot_warped_field(self.mesh, name=name, cmap=cmap, warp_scale=warp_scale)

    @staticmethod
    def from_random_gaussians(mode, num_gaussians, width, height, minimum_sigma, maximum_sigma):
        scalar_field = GaussianBuilder.generate_random_gaussians(
            num_gaussians, width, height, minimum_sigma, maximum_sigma, mode=mode
        )
        structured_grid = FieldBuilder.create_structured_grid(scalar_field)
        triangulated_mesh = FieldBuilder.triangulate(structured_grid)
        return Field(mesh=triangulated_mesh)
