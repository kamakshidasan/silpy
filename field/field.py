import pyvista as pv
from .gaussian_builder import GaussianBuilder
from .field_builder import FieldBuilder
from ..debug.field import plot_field, plot_warped_field, plot_field_3d
from .field_builder_3d import FieldBuilder3D
from .gaussian_builder_3d import GaussianBuilder3D

class Field:
    def __init__(self, mesh=None, filename=None):
        if filename is not None:
            self.mesh = pv.read(filename)
        else:
            self.mesh = mesh

    def compute_field(self, name):
        """
        Stub for computing a scalar field.
        Replace this with actual field computation logic.
        """
        # Stub: assign Z coordinate as dummy field
        values = self.mesh.points[:, 2]
        self.mesh[name] = values

    def get_field(self, name):
        # Retrieve a scalar field by name.
        return self.mesh[name]

    def load(self, filename):
        # init class with mesh as None and then load()
        self.mesh = pv.read(filename)

    def save(self, filename):
        self.mesh.save(filename)

    def plot(self, name=None, cmap="viridis", warp=False, warp_scale=5.0):
        """
        Visualize the mesh colored by a scalar field.
        """
        # Unpack point_data.keys():
        # first_name gets the first field name, *_ ignores the rest
        first_name, *_ = self.mesh.point_data.keys()
        name = name if name is not None else first_name

        if not warp:
            plot_field(self.mesh, name=name, cmap=cmap)
        else:
            plot_warped_field(self.mesh, name=name, cmap=cmap, warp_scale=warp_scale)

    def plot_3d(self, name=None, cmap="coolwarm"):
        first_name, *_ = self.mesh.point_data.keys()
        name = name if name is not None else first_name
        plot_field_3d(self.mesh, name=name, cmap=cmap)

    @classmethod
    def from_random_gaussians(
        cls,
        mode,
        num_gaussians,
        width,
        height,
        minimum_sigma,
        maximum_sigma
    ):
        # Factory: generate array, build mesh, wrap in Field
        scalar_field = GaussianBuilder.generate_random_gaussians(
            num_gaussians,
            width,
            height,
            minimum_sigma,
            maximum_sigma,
            mode=mode
        )
        structured_grid = FieldBuilder.create_structured_grid(scalar_field)
        triangulated_mesh = FieldBuilder.triangulate(structured_grid)
        return cls(mesh=triangulated_mesh)


    @classmethod
    def from_random_gaussians_3d(
        cls,
        mode,
        num_gaussians,
        width,
        height,
        depth,
        minimum_sigma,
        maximum_sigma
    ):
        # Factory: generate array, build mesh, wrap in Field
        scalar_field = GaussianBuilder3D.generate_random_gaussians(
            num_gaussians,
            width,
            height,
            depth,
            minimum_sigma,
            maximum_sigma,
            mode=mode
        )
        structured_grid = FieldBuilder3D.create_structured_grid(scalar_field, field_name="gaussian")
        triangulated_mesh = FieldBuilder3D.tetrahedralize_structured_grid(structured_grid, field_name="gaussian")
        return cls(mesh=triangulated_mesh)

    # scalar_field = np.array([
    #     [9, 2, 5],
    #     [4, 8, 3],
    #     [7, 1, 6]
    # ], dtype=np.float32)
    # field = Field.from_array(scalar_field, 'custom')

    @classmethod
    def from_array(cls, scalar_field, field_name='gaussian'):
        structured_grid = FieldBuilder.create_structured_grid(scalar_field, field_name)
        triangulated_mesh = FieldBuilder.triangulate(structured_grid, field_name)
        return cls(mesh=triangulated_mesh)


    # this function exists to check the LTS mesh
    @classmethod
    def from_points(cls, point_list, face_list, field_name="custom"):
        mesh = FieldBuilder.from_points(point_list, face_list, field_name)
        return cls(mesh=mesh)
