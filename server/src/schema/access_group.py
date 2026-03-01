from pydantic import BaseModel
from pydantic.config import ConfigDict
from typing import Optional


class AccessGroupBase(BaseModel):
    name: str


class AccessGroupCreate(AccessGroupBase):
    pass


class AccessGroupUpdate(AccessGroupBase):
    name: Optional[str] = None


class AccessGroupInDB(AccessGroupBase):
    id: int

    model_config = ConfigDict(from_attributes=True)