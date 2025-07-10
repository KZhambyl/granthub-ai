from sqlalchemy import Column, Integer, String, Date
from app.db import Base

class Grant(Base):
    __tablename__ = "grants"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    deadline = Column(Date, nullable=True)
    amount = Column(String, nullable=True)
