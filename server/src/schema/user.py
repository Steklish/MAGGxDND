from pydantic import BaseModel
from pydantic.config import ConfigDict
from typing import Optional


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str
    group_id: Optional[int] = None

class UserCreateHashed(UserBase):
    hashed_password: str
    group_id: Optional[int] = None


class UserUpdate(UserBase):
    password: Optional[str] = None
    group_id: Optional[int] = None


class UserUpdateHashed(UserBase):
    hashed_password: Optional[str] = None
    group_id: Optional[int] = None


class UserInDB(UserBase):
    id: int
    group_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)