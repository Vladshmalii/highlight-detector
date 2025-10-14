from app.core.celery_app import celery_app
from app.services.detector import GameDetector
from app.services.scorers import HighlightScorer
from app.models.video import Video
from app.core.enum import VideoStatus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from datetime import datetime
import os
import logging
import subprocess
import time

logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


@celery_app.task(bind=True, max_retries=3)
def process_video(self, video_id: int):
    db = SessionLocal()
    start_time = time.time()

    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.error(f"Video {video_id} not found")
            return

        video.status = VideoStatus.PROCESSING
        db.commit()

        video_path = os.path.join(settings.VIDEO_UPLOAD_DIR, video.filename)

        detector = GameDetector(video.game_type)
        all_events = detector.detect_all(video_path)

        scorer = HighlightScorer(video.game_type)
        scored_events = scorer.score_all(all_events)

        min_spacing = 30.0 if video.game_type == 'cs2' else 60.0
        top_highlights = scorer.select_top_k(scored_events, k=5, min_spacing=min_spacing)

        output_dir = os.path.join(settings.VIDEO_UPLOAD_DIR, f"highlights_{video_id}")
        os.makedirs(output_dir, exist_ok=True)

        for idx, highlight in enumerate(top_highlights):
            output_file = os.path.join(output_dir, f"highlight_{idx + 1}.mp4")
            start = max(0, highlight['timestamp'] - 5)
            duration = 8

            subprocess.run([
                'ffmpeg', '-y', '-ss', str(start), '-i', video_path,
                '-t', str(duration), '-c:v', 'libx264', '-c:a', 'aac',
                '-preset', 'fast', output_file
            ], check=True, capture_output=True)

            highlight['filename'] = f"highlight_{idx + 1}.mp4"
            highlight['path'] = output_file

        processing_time = time.time() - start_time

        video.highlights = top_highlights
        video.total_events = len(all_events)
        video.processing_time = processing_time
        video.status = VideoStatus.COMPLETED
        video.processed_at = datetime.utcnow()
        video.video_metadata = {
            'all_events_count': len(all_events),
            'selected_highlights': len(top_highlights),
            'game_type': video.game_type.value
        }
        db.commit()

        logger.info(
            f"Video {video_id} processed: {len(all_events)} events, {len(top_highlights)} highlights, {processing_time:.1f}s")

    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        if video:
            video.status = VideoStatus.FAILED
            db.commit()
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()