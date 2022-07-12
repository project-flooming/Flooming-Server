import os.path

import uvicorn
from fastapi import FastAPI, UploadFile, Depends
from sqlalchemy.orm import Session

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

from database.config import SessionLocal, engine, Base
from database.models import Picture, Photo, Flower
import uuid
import logging
from ai.inference import classify

# 데이터베이스 스키마 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()


# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 디비 init
@app.on_event("startup")
async def init(db: Session = Depends(get_db)):
    return True


# 미들웨어를 통한 통합 로깅 및 예외처리
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    logger.info("Request start")
    try:
        return await call_next(request)
    except Exception as e:
        logger.warning(f"Request failed: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=400)
    finally:
        logger.info("Request end")


# 사진 업로드 후 꽃 분류
@app.post("/photo")
async def upload_photo(file: UploadFile, db: Session = Depends(get_db)):
    # 서버 로컬 스토리지에 이미지 저장
    UPLOAD_DIR = "./photo"

    content = await file.read()
    logging.info(f"original filename = {file.filename}")
    filename = f"{str(uuid.uuid4())}.jpg"
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as fp:
        fp.write(content)
    src = f"{UPLOAD_DIR}/{filename}"

    # 디비에 저장
    db.add(Photo(filename=filename, src=src))
    db.commit()

    # 꽃 분류
    result_response = []
    for result in classify(src):
        flower: Flower = db.query(Flower).filter_by(kor_name=result["type"]).first()
        data = {
            "probability": result["probability"],
            "kor_name": flower.kor_name,
            "eng_name": flower.eng_name,
            "flower_language": flower.flower_language
        }
        result_response.append(data)

    logger.info(f"classify results = {result_response}")

    saved_data: Photo = db.query(Photo).filter_by(filename=filename).first()
    return {"result": result_response}




# 사진 가져오기
@app.get("/photo/{photo_id}")
async def get_photo_by_id(photo_id, db: Session = Depends(get_db)):
    return db.query(Photo).filter_by(photo_id=photo_id).first()


# 사진 -> 그림 변환
@app.get("/picture/{filename}")
async def create_picture(filename):
    # 그림 변환
    return True


# 사진 다운로드
@app.get("/download/photo")
async def download_photo():
    return True


# 그림 다운로드
@app.get("/download/picture")
async def download_picture():
    return True


# 갤러리 - 사진/그림 리스트 반환
@app.get("/gallery")
async def get_all_gallery(db: Session = Depends(get_db)):
    result = db.query(Picture).all()
    return result

@app.get("/test")
async def test():
    return {"test" : "success"}

if __name__ == "__main__":
    uvicorn.run(app)