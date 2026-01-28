import cv2
import numpy as np

newImageInfo = (600, 600, 3)
dst = np.zeros(newImageInfo, np.uint8)

cv2.line(dst, (100, 100), (200, 200), (255, 0, 0))

cv2.line(dst, (80, 100), (80, 200), (0, 255, 0), 10)
cv2.line(dst, (220, 100), (220, 200), (255, 0, 0), 10, cv2.LINE_AA)


cv2.imshow('dst', dst)
cv2.waitKey(0)
