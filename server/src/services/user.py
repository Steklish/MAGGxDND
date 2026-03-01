from typing import Optional, List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from server.src.models import User, AccessGroup
from server.src.schema import (
    UserCreate, 
    UserUpdate, 
    UserInDB,
    AccessGroupCreate, 
    AccessGroupUpdate, 
    AccessGroupInDB
)
from server.src.repositories import user_repo, access_group_repo
from server.src.schema.user import UserCreateHashed, UserUpdateHashed
from server.src.utils import security
from server.src.utils.security import get_password_hash, verify_password


class AccessGroupService:
    def create_access_group(self, db: Session, access_group_in: AccessGroupCreate) -> AccessGroupInDB:
        db_access_group = access_group_repo.create(db, obj_in=access_group_in)
        return AccessGroupInDB.model_validate(db_access_group)

    def get_access_group(self, db: Session, access_group_id: int) -> Optional[AccessGroupInDB]:
        db_access_group = access_group_repo.get(db, id=access_group_id)
        if db_access_group:
            return AccessGroupInDB.model_validate(db_access_group)
        return None

    def get_access_group_by_name(self, db: Session, name: str) -> Optional[AccessGroupInDB]:
        db_access_group = access_group_repo.get_by_name(db, name=name)
        if db_access_group:
            return AccessGroupInDB.model_validate(db_access_group)
        return None

    def get_access_groups(self, db: Session, skip: int = 0, limit: int = 100) -> List[AccessGroupInDB]:
        db_access_groups = access_group_repo.get_multi(db, skip=skip, limit=limit)
        return [AccessGroupInDB.model_validate(ag) for ag in db_access_groups]

    def update_access_group(self, db: Session, access_group_id: int, 
                           access_group_in: AccessGroupUpdate) -> Optional[AccessGroupInDB]:
        db_access_group = access_group_repo.get(db, id=access_group_id)
        if not db_access_group:
            return None
        updated_access_group = access_group_repo.update(db, db_obj=db_access_group, obj_in=access_group_in)
        return AccessGroupInDB.model_validate(updated_access_group)

    def delete_access_group(self, db: Session, access_group_id: int) -> bool:
        db_access_group = access_group_repo.get(db, id=access_group_id)
        if not db_access_group:
            return False
        db.delete(db_access_group)
        db.commit()
        return True


class UserService:
    def create_user(self, db: Session, user_in: UserCreate) -> UserInDB:
        # Check if the username already exists
        existing_user = user_repo.get_by_username(db, user_in.username)
        if existing_user:
            raise ValueError(f"Username '{user_in.username}' already exists")
        
        # If group_id is provided and not None, validate that the group exists
        if user_in.group_id is not None and user_in.group_id != 0:
            group = access_group_repo.get(db, id=user_in.group_id)
            if not group:
                raise ValueError(f"Access group with ID {user_in.group_id} does not exist")
        elif user_in.group_id == 0:
            # If group_id is 0, treat it as None (no group)
            # Create a copy of user_in with group_id as None
            user_in = user_in.model_copy(update={"group_id": None})
        
        # Hash the password before storing, ensuring it's not longer than 72 characters (bcrypt limit)
        hashed_password = get_password_hash(user_in.password)
        user_in_db = user_in.model_copy(update={"password": hashed_password})
        user_in_db = UserCreateHashed(
            username=user_in.username,
            hashed_password=hashed_password,
            group_id=user_in.group_id
        )
        db_user = user_repo.create(db, obj_in=user_in_db)
        return UserInDB.model_validate(db_user)

    def get_user(self, db: Session, user_id: int) -> Optional[UserInDB]:
        db_user = user_repo.get(db, id=user_id)
        if db_user:
            return UserInDB.model_validate(db_user)
        return None

    def get_user_by_username(self, db: Session, username: str) -> Optional[UserInDB]:
        db_user = user_repo.get_by_username(db, username=username)
        if db_user:
            return UserInDB.model_validate(db_user)
        return None

    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[UserInDB]:
        db_users = user_repo.get_multi(db, skip=skip, limit=limit)
        return [UserInDB.model_validate(user) for user in db_users]

    def update_user(self, db: Session, user_id: int, user_in: UserUpdate) -> Optional[UserInDB]:
        db_user = user_repo.get(db, id=user_id)
        if not db_user:
            return None
        
        # Prepare updated data, handling password hashing and group validation if needed
        update_data = user_in.model_dump(exclude_unset=True)
        
        if "password" in update_data and update_data["password"]:
            hashed_password = security.get_password_hash(update_data["password"])
            update_data["hashed_password"] = hashed_password
            # Remove the plain-text password before it goes any further
            del update_data["password"]
            
        # Step 4: Handle group validation (your existing logic is good)
        if "group_id" in update_data and update_data["group_id"]:
            group = access_group_repo.get(db, id=update_data["group_id"])
            if not group:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Access group with ID {update_data['group_id']} does not exist"
                )
        elif "group_id" in update_data and update_data["group_id"] == 0:
            update_data["group_id"] = None
        
        # Step 5: Create an instance of the INTERNAL schema (`UserUpdateHashed`)
        user_data_for_db = UserUpdateHashed(**update_data)
        
        updated_user = user_repo.update(db, db_obj=db_user, obj_in=user_data_for_db)
        return UserInDB.model_validate(updated_user)

    def delete_user(self, db: Session, user_id: int) -> bool:
        db_user = user_repo.get(db, id=user_id)
        if not db_user:
            return False
        db.delete(db_user)
        db.commit()
        return True


# Create instances of the services
user_service = UserService()
access_group_service = AccessGroupService()