import cv2
import numpy as np
from typing import List, Dict, Optional
from app.services.ocr_engine import OCREngine
from app.services.audio_analyzer import AudioAnalyzer
from app.core.enum import GameType, EventType


class GameDetector:
    def __init__(self, game_type: GameType):
        self.game_type = game_type
        self.ocr = OCREngine()
        self.audio = AudioAnalyzer()
        self.frame_buffer = []
        self.events = []

    def detect_all(self, video_path: str) -> List[Dict]:
        audio_data, _ = self.audio.load_audio(video_path)
        audio_peaks = self.audio.detect_intensity_peaks(audio_data)

        visual_events = self._process_video(video_path)

        combined = self._merge_events(visual_events, audio_peaks)
        return combined

    def _process_video(self, video_path: str) -> List[Dict]:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_idx = 0
        frame_skip = 5
        events = []

        while cap.isOpened():
            ret = cap.grab()
            if not ret:
                break

            if frame_idx % frame_skip == 0:
                _, frame = cap.retrieve()
                timestamp = frame_idx / fps

                event = self._detect_frame(frame, timestamp)
                if event:
                    events.append(event)

            frame_idx += 1

        cap.release()
        return events

    def _detect_frame(self, frame: np.ndarray, timestamp: float) -> Optional[Dict]:
        h, w = frame.shape[:2]

        if self.game_type == GameType.CS2:
            return self._detect_cs2_frame(frame, timestamp, w, h)
        elif self.game_type == GameType.DOTA2:
            return self._detect_dota2_frame(frame, timestamp, w, h)

        return None

    def _detect_cs2_frame(self, frame: np.ndarray, timestamp: float, w: int, h: int) -> Optional[Dict]:
        killfeed_roi = (int(w * 0.8), int(h * 0.05), int(w * 0.18), int(h * 0.25))
        text = self.ocr.extract_text(frame, killfeed_roi)

        if not text:
            return None

        event = {
            'timestamp': timestamp,
            'text': text,
            'type': EventType.KILL.value
        }

        if 'headshot' in text:
            event['special'] = 'headshot'
        if 'wallbang' in text:
            event['special'] = 'wallbang'

        return event

    def _detect_dota2_frame(self, frame: np.ndarray, timestamp: float, w: int, h: int) -> Optional[Dict]:
        banner_roi = (int(w * 0.35), int(h * 0.05), int(w * 0.3), int(h * 0.1))
        text = self.ocr.extract_text(frame, banner_roi)

        if not text:
            return None

        event = {
            'timestamp': timestamp,
            'text': text,
            'type': EventType.KILL.value
        }

        if 'rampage' in text:
            event['type'] = EventType.RAMPAGE.value
        elif 'ultra kill' in text:
            event['type'] = EventType.MULTI_KILL.value
        elif 'triple kill' in text:
            event['type'] = EventType.MULTI_KILL.value

        return event

    def _merge_events(self, visual: List[Dict], audio_peaks: np.ndarray) -> List[Dict]:
        for peak_time in audio_peaks:
            matching = [e for e in visual if abs(e['timestamp'] - peak_time) < 3.0]

            if not matching:
                visual.append({
                    'timestamp': float(peak_time),
                    'type': EventType.TEAMFIGHT.value,
                    'source': 'audio',
                    'text': ''
                })

        return sorted(visual, key=lambda x: x['timestamp'])