from typing import List, Dict
from app.core.enum import GameType, EventType


class HighlightScorer:
    def __init__(self, game_type: GameType):
        self.game_type = game_type

        if game_type == GameType.CS2:
            self.scorer = CS2Scorer()
        elif game_type == GameType.DOTA2:
            self.scorer = Dota2Scorer()

    def score_all(self, events: List[Dict]) -> List[Dict]:
        for event in events:
            event['score'] = self.scorer.calculate_score(event)
        return events

    def select_top_k(self, events: List[Dict], k: int = 5, min_spacing: float = 30.0) -> List[Dict]:
        sorted_events = sorted(events, key=lambda x: x['score'], reverse=True)
        selected = []

        for event in sorted_events:
            if len(selected) >= k:
                break

            has_conflict = any(abs(event['timestamp'] - s['timestamp']) < min_spacing for s in selected)

            if not has_conflict:
                selected.append(event)

        return selected


class CS2Scorer:
    def __init__(self):
        self.base_scores = {
            EventType.KILL.value: 100,
            EventType.MULTI_KILL.value: 400,
            EventType.ACE.value: 1200,
            EventType.CLUTCH.value: 800
        }

        self.special_multipliers = {
            'headshot': 1.2,
            'wallbang': 1.5,
            'noscope': 1.8
        }

    def calculate_score(self, event: Dict) -> float:
        base = self.base_scores.get(event['type'], 100)
        multiplier = 1.0

        special = event.get('special')
        if special and special in self.special_multipliers:
            multiplier *= self.special_multipliers[special]

        return base * multiplier


class Dota2Scorer:
    def __init__(self):
        self.base_scores = {
            EventType.KILL.value: 100,
            EventType.MULTI_KILL.value: 500,
            EventType.RAMPAGE.value: 1500,
            EventType.TEAMFIGHT.value: 600,
            EventType.OBJECTIVE.value: 800
        }

    def calculate_score(self, event: Dict) -> float:
        base = self.base_scores.get(event['type'], 100)

        if 'rampage' in event.get('text', ''):
            return 1500
        elif 'ultra kill' in event.get('text', ''):
            return 900
        elif 'triple kill' in event.get('text', ''):
            return 500

        return base