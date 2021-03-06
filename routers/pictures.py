from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from ai.inference import generate
from database.config import get_db
from database.models import Picture, Gallery, Photo
from database.schemas import GalleryDto, PictureRequest
from loguru import logger

router = APIRouter()


# 사용자가 선택한 타입으로 사전 업데이트 및 사진 -> 그림 변환
@router.post("/picture")
async def create_picture(form: PictureRequest, db: Session = Depends(get_db)):
    try:
        src = db.query(Photo).filter_by(photo_id=form.photo_id).first().src

        # 그림 변환
        generate(src)

        # 그림 디비 저장
        db_picture: Picture = Picture(src=src)
        db.add(db_picture)
        db.commit()
        db.refresh(db_picture)

        return {
            "photo_id": form.photo_id,
            "picture_id": db_picture.picture_id
        }
    except Exception as e:
        logger.warning(f"Drawing error : {str(e)}")
        raise HTTPException(status_code=400, detail="그림 그리는데 오류가 발생 했습니다.")


async def paging(db, page):
    unit_per_page = 5
    offset = page * unit_per_page
    result_from_db = db.query(Gallery).order_by(desc(Gallery.created_time)).offset(offset).limit(unit_per_page).all()
    result = []
    for post in result_from_db:
        result.append(GalleryDto(photo_id=post.photo_id, picture_id=post.picture_id, comment=post.comment))
    return result


# 갤러리 - 사진/그림 업로드
@router.post("/gallery")
async def create_gallery(form: GalleryDto, db: Session = Depends(get_db)):
    db.add(Gallery(photo_id=form.photo_id, picture_id=form.picture_id, comment=form.comment))
    db.commit()
    return {"result": await paging(db, page=0)}


# 갤러리 - 사진/그림 리스트 반환
@router.get("/gallery")
async def get_all_gallery(page: int, db: Session = Depends(get_db)):
    return {"result": await paging(db, page)}


@router.get("/picture/{picture_id}")
async def get_picture(picture_id: int, db: Session = Depends(get_db)):
    find_picture: Picture = db.query(Picture).filter_by(picture_id=picture_id).first()
    if find_picture is None:
        raise HTTPException(status_code=400, detail="그림 조회 실패 : 해당 사진을 찾을 수 없습니다.")
    return FileResponse(find_picture.src)


# 그림 다운로드
@router.get("/download/picture/{picture_id}")
async def download_picture(picture_id: int, db: Session = Depends(get_db)):
    find_picture: Picture = db.query(Picture).filter_by(picture_id=picture_id).first()
    if find_picture is None:
        raise HTTPException(status_code=400, detail="그림 다운로드 실패 : 해당 사진을 찾을 수 없습니다.")
    return FileResponse(find_picture.src)
