# gaussian_builder_3d.py
import numpy as np
import random

class GaussianBuilder3D:
    @staticmethod
    def create_gaussian(grid_x, grid_y, grid_z, center_position, sigma_value):
        # Compute a 3D Gaussian at each grid point
        gaussian_map = np.exp(
            -(((grid_x - center_position[0])**2 +
                (grid_y - center_position[1])**2 +
                (grid_z - center_position[2])**2) /
               (2 * sigma_value**2))
        )
        return gaussian_map.astype(np.float32)

    @staticmethod
    def generate_meshgrid(width, height, depth):
        # Build meshgrid for volume coordinates
        x_coordinates = np.linspace(0, width - 1, width, dtype=np.float32)
        y_coordinates = np.linspace(0, height - 1, height, dtype=np.float32)
        z_coordinates = np.linspace(0, depth - 1, depth, dtype=np.float32)
        return np.meshgrid(x_coordinates, y_coordinates, z_coordinates, indexing='xy')

    @staticmethod
    def sample_random_center_and_sigma(width, height, depth, minimum_sigma, maximum_sigma):
        # Sample a random center within bounds and a random sigma
        random_center_x = np.float32(random.randint(0, width - 1))
        random_center_y = np.float32(random.randint(0, height - 1))
        random_center_z = np.float32(random.randint(0, depth - 1))
        random_sigma = np.float32(random.uniform(minimum_sigma, maximum_sigma))
        return (random_center_x, random_center_y, random_center_z), random_sigma

    @staticmethod
    def normalize_array(array, minimum_value, maximum_value):
        # Normalize array to a new range [minimum_value, maximum_value]
        array_minimum = array.min()
        array_maximum = array.max()
        if array_maximum == array_minimum:
            return np.zeros_like(array, dtype=np.float32)

        normalized = (array - array_minimum) / (array_maximum - array_minimum)
        scaled = normalized * (maximum_value - minimum_value) + minimum_value
        return scaled.astype(np.float32)

    @classmethod
    def generate_random_gaussians(
        cls,
        num_gaussians,
        width,
        height,
        depth,
        minimum_sigma,
        maximum_sigma,
        mode='positive'
    ):
        # Generate multiple random 3D Gaussians in positive, negative, or mixed modes
        if mode not in ('positive', 'negative', 'mixed'):
            raise ValueError(f'Unknown mode: {mode}')

        output_array = np.zeros((height, width, depth), dtype=np.float32)
        grid_x, grid_y, grid_z = cls.generate_meshgrid(width, height, depth)

        # Prepare sign sequence based on mode
        if mode == 'positive':
            sign_sequence = [1] * num_gaussians
            normalization_range = (0.0, 1.0)
        elif mode == 'negative':
            sign_sequence = [-1] * num_gaussians
            normalization_range = (-1.0, 0.0)
        else:
            sign_sequence = [random.choice([1, -1]) for _ in range(num_gaussians)]
            normalization_range = (-1.0, 1.0)

        # Accumulate Gaussians with corresponding signs
        for sign in sign_sequence:
            center_position, sigma_value = cls.sample_random_center_and_sigma(
                width, height, depth, minimum_sigma, maximum_sigma
            )
            gaussian_values = cls.create_gaussian(
                grid_x, grid_y, grid_z, center_position, sigma_value
            )
            output_array += sign * gaussian_values

        min_norm, max_norm = normalization_range
        return cls.normalize_array(output_array, min_norm, max_norm)
