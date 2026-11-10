from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.video import Video
from app.tasks.video_tasks import process_video
from app.core.config import settings
from app.core.enum import GameType
from app.core.paths import new_upload_name, resolve_in_dir
import os

router = APIRouter()


def get_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload")
async def upload_video(
        file: UploadFile = File(...),
        game_type: GameType = GameType.CS2,
        db: Session = Depends(get_db)
):
    try:
        stored_name = new_upload_name(file.filename)
        file_path = resolve_in_dir(settings.VIDEO_UPLOAD_DIR, stored_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    os.makedirs(settings.VIDEO_UPLOAD_DIR, exist_ok=True)

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    size = 0
    with open(file_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                buffer.close()
                os.remove(file_path)
                raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB")
            buffer.write(chunk)

    video = Video(filename=stored_name, game_type=game_type, status="pending")
    db.add(video)
    db.commit()
    db.refresh(video)

    process_video.delay(video.id)

    return {"video_id": video.id, "game_type": game_type.value, "status": "pending"}


@router.get("/status/{video_id}")
def get_status(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return {
        "video_id": video.id,
        "game_type": video.game_type.value,
        "status": video.status.value,
        "highlights": video.highlights,
        "total_events": video.total_events,
        "processing_time": video.processing_time,
        "created_at": video.created_at,
        "processed_at": video.processed_at
    }