from cv2 import (
    getStructuringElement,
    MORPH_ELLIPSE
)

# Kernel for morphological operation opening
KERNEL3 = getStructuringElement(
    MORPH_ELLIPSE,
    (3, 3), (-1, -1)
)

KERNEL20 = getStructuringElement(
    MORPH_ELLIPSE,
    (5, 5), (-1, -1)
)
