import librosa
import numpy as np
from scipy.signal import find_peaks
from typing import List, Tuple


class AudioAnalyzer:
    def __init__(self, sr: int = 22050):
        self.sr = sr

    def load_audio(self, video_path: str) -> Tuple[np.ndarray, int]:
        audio, sr = librosa.load(video_path, sr=self.sr, mono=True)
        return audio, sr

    def detect_intensity_peaks(self, audio: np.ndarray, threshold_multiplier: float = 2.5) -> np.ndarray:
        intensity = audio ** 2

        window_size = self.sr // 2
        kernel = np.ones(window_size) / window_size
        smoothed = np.convolve(intensity, kernel, mode='same')

        mean_intensity = np.mean(smoothed)
        std_intensity = np.std(smoothed)
        threshold = mean_intensity + threshold_multiplier * std_intensity

        peaks, _ = find_peaks(smoothed, height=threshold, distance=self.sr * 5)
        peak_times = librosa.frames_to_time(peaks, sr=self.sr)

        return peak_times

    def calculate_rms_timeline(self, audio: np.ndarray, frame_length: int = 2048) -> np.ndarray:
        rms = librosa.feature.rms(y=audio, frame_length=frame_length)[0]
        return rms