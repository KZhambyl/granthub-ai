from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.models import Grant
from app.schemas.grant import GrantCreate, GrantOut
from app.db import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/grants", response_model=List[GrantOut])
def get_grants(db: Session = Depends(get_db)):
    return db.query(Grant).all()


@router.post("/grants", response_model=GrantOut)
def create_grant(grant: GrantCreate, db: Session = Depends(get_db)):
    new_grant = Grant(**grant.dict())
    db.add(new_grant)
    db.commit()
    db.refresh(new_grant)
    return new_grant


@router.put("/grants/{grant_id}", response_model=GrantOut)
def update_grant(
    grant_id: int = Path(..., description="ID гранта для обновления"),
    grant_update: GrantCreate = Depends(),
    db: Session = Depends(get_db)
):
    grant = db.query(Grant).filter(Grant.id == grant_id).first()
    if not grant:
        raise HTTPException(status_code=404, detail="Грант не найден")

    for field, value in grant_update.dict().items():
        setattr(grant, field, value)

    db.commit()
    db.refresh(grant)
    return grant


@router.delete("/grants/{grant_id}")
def delete_grant(grant_id: int, db: Session = Depends(get_db)):
    grant = db.query(Grant).filter(Grant.id == grant_id).first()
    if not grant:
        raise HTTPException(status_code=404, detail="Грант не найден")

    db.delete(grant)
    db.commit()
    return {"detail": f"Грант #{grant_id} удалён"}
