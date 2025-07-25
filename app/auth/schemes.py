from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import List




class UserCreateModel(BaseModel):
    first_name: str = Field(max_length=10)
    last_name: str = Field(max_length=10)
    username: str = Field(max_length=20)
    email: str = Field(max_length=30)
    password: str = Field(min_length=8)

class UserModel(BaseModel):
    uid : uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_verified: bool
    password_hash: str = Field(exclude=True)
    created_at: datetime
    updated_at: datetime

class UserLoginModel(BaseModel):
    email: str = Field(max_length=30)
    password: str = Field(min_length=8)
    

class EmailModel(BaseModel):
    addresses: List[str]

class PasswordResetRequestModel(BaseModel):
    email: str
        
class PasswordResetConfirmModel(BaseModel):
    new_password: str
    confirm_new_password: str
