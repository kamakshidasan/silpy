import numpy as np

REGULAR = np.uint8(0)
MAXIMUM = np.uint8(1)
MINIMUM = np.uint8(2)
BOTH = np.uint8(3)
SPLIT = np.uint8(4)
JOIN = np.uint8(5)

TYPE_STRINGS = {
    REGULAR: "regular",
    MAXIMUM: "maximum",
    MINIMUM: "minimum",
    BOTH: "both",
    SPLIT: "split",
    JOIN: "join",
}

def get_point_type(point_type):
    return TYPE_STRINGS[point_type]
