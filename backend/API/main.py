from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.connection import Base, engine, get_db
from backend.models.phone_record import PhoneRecord
from backend.schemas import PhoneCreate, PhoneRead

Base.metadata.create_all(bind=engine)

app = FastAPI(title="VAIU Phone API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/phone", response_model=PhoneRead, status_code=status.HTTP_201_CREATED)
def create_phone_record(
    payload: PhoneCreate, db: Session = Depends(get_db)
) -> PhoneRecord:
    record = PhoneRecord(
        rawTranscript=payload.rawTranscript,
        parsedNumber=payload.parsedNumber,
        language=payload.language,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.get("/api/phone", response_model=list[PhoneRead])
def list_phone_records(db: Session = Depends(get_db)) -> list[PhoneRecord]:
    return list(db.scalars(select(PhoneRecord).order_by(PhoneRecord.id.desc())))


@app.delete("/api/phone/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_phone_record(record_id: int, db: Session = Depends(get_db)) -> Response:
    record = db.get(PhoneRecord, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone record not found",
        )
    db.delete(record)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
