from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
import uuid
from datetime import datetime



class User(SQLModel, table=True):
    __tablename__ = "users"

    uid : uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default = uuid.uuid4
        )
    )
    username: str
    email: str
    first_name: str
    last_name: str
    role: str = Field(
        sa_column=Column(pg.VARCHAR, nullable=False, server_default="user")
    )
    is_verified: bool = Field(default=False)
    password_hash: str = Field(exclude=True)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

    def __repr__(self):
        return f"<User {self.username}>"