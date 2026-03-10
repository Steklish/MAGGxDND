from typing import Optional
from sqlalchemy.orm import Session

from backend.src.models.user import AccessGroup, User
from backend.src.schema.access_group import AccessGroupCreate, AccessGroupUpdate
from backend.src.schema.user import UserCreateHashed, UserUpdateHashed
from .base import BaseRepository


class UserRepository(BaseRepository[User, UserCreateHashed, UserUpdateHashed]):
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def update(self, db: Session, *, db_obj: User, obj_in: UserUpdateHashed) -> User:
        for field in obj_in.__fields__:
            if hasattr(db_obj, field) and getattr(obj_in, field) is not None:
                setattr(db_obj, field, getattr(obj_in, field))
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class AccessGroupRepository(BaseRepository[AccessGroup, AccessGroupCreate, AccessGroupUpdate]):
    def get_by_name(self, db: Session, name: str) -> Optional[AccessGroup]:
        return db.query(AccessGroup).filter(AccessGroup.name == name).first()

    def update(self, db: Session, *, db_obj: AccessGroup, obj_in: AccessGroupUpdate) -> AccessGroup:
        for field in obj_in.__fields__:
            if hasattr(db_obj, field) and getattr(obj_in, field) is not None:
                setattr(db_obj, field, getattr(obj_in, field))
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


# Create instances of the repositories
user_repo = UserRepository(User)
access_group_repo = AccessGroupRepository(AccessGroup)