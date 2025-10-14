import cv2
import numpy as np
import easyocr
from typing import Optional, Tuple


class OCREngine:
    def __init__(self, languages=['en']):
        self.reader = easyocr.Reader(languages, gpu=True)

    def preprocess_roi(self, frame: np.ndarray, roi: Tuple[int, int, int, int]) -> np.ndarray:
        x, y, w, h = roi
        cropped = frame[y:y + h, x:x + w]

        gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        scaled = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        kernel = np.ones((3, 3), np.uint8)
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        return morph

    def extract_text(self, frame: np.ndarray, roi: Tuple[int, int, int, int]) -> str:
        processed = self.preprocess_roi(frame, roi)
        results = self.reader.readtext(processed, detail=0, paragraph=True)
        return ' '.join(results).lower() if results else ""