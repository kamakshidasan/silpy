import numpy as np
import random

class GaussianBuilder:
    @staticmethod
    def create_gaussian(grid_x, grid_y, center, sigma):
        # Compute a 2D Gaussian at each grid point
        center_x, center_y = center[0], center[1]
        delta_x, delta_y = grid_x - center_x, grid_y - center_y
        squared_distance = delta_x**2 + delta_y**2
        denominator = 2 * (sigma**2)
        gaussian_map = np.exp(-(squared_distance / denominator))
        return gaussian_map.astype(np.float32)

    @staticmethod
    def generate_meshgrid(width, height):
        # Build meshgrid for image coordinates
        x_coordinates = np.linspace(0, width - 1, width, dtype=np.float32)
        y_coordinates = np.linspace(0, height - 1, height, dtype=np.float32)
        return np.meshgrid(x_coordinates, y_coordinates)

    @staticmethod
    def sample_random_parameters(width, height, minimum_sigma, maximum_sigma):
        # Sample random Gaussian parameters
        random_center_x = np.float32(random.randint(0, width - 1))
        random_center_y = np.float32(random.randint(0, height - 1))
        random_sigma = np.float32(random.uniform(minimum_sigma, maximum_sigma))
        return (random_center_x, random_center_y), random_sigma

    @staticmethod
    def normalize_grid(grid, grid_minimum, grid_maximum):
        # Normalize grid to a new range [grid_minimum, grid_maximum]
        current_minimum, current_maximum = grid.min(), grid.max()
        normalized_grid = (grid - current_minimum) / (current_maximum - current_minimum)
        scaled_grid = normalized_grid * (grid_maximum - grid_minimum) + grid_minimum
        return scaled_grid.astype(np.float32)

    @staticmethod
    def generate_random_gaussians(num_gaussians, width, height, minimum_sigma, maximum_sigma, mode="positive"):
        # Generate multiple random Gaussians in positive, negative, or mixed modes
        output_array = np.zeros((height, width), dtype=np.float32)
        grid_x, grid_y = GaussianBuilder.generate_meshgrid(width, height)

        # Prepare sign sequence based on mode
        if mode == "positive":
            sign_sequence = random.choices([1], k=num_gaussians)
            normalization_range = (np.float32(0.0), np.float32(1.0))
        elif mode == "negative":
            sign_sequence = random.choices([-1], k=num_gaussians)
            normalization_range = (np.float32(-1.0), np.float32(0.0))
        else:
            sign_sequence = random.choices([1, -1], k=num_gaussians)
            normalization_range = (np.float32(-1.0), np.float32(1.0))

        # Accumulate Gaussians with corresponding signs
        for sign_value in sign_sequence:
            center, sigma = GaussianBuilder.sample_random_parameters(width, height, minimum_sigma, maximum_sigma)
            gaussian_values = GaussianBuilder.create_gaussian(grid_x, grid_y, center, sigma)
            output_array += sign_value * gaussian_values

        grid_minimum, grid_maximum = normalization_range
        return GaussianBuilder.normalize_grid(output_array, grid_minimum, grid_maximum)
