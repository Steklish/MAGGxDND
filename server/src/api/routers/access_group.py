from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from server.src.database.session import get_db
from server.src.schema.access_group import AccessGroupCreate, AccessGroupInDB, AccessGroupUpdate
from server.src.services.user import access_group_service

router = APIRouter(prefix="/access-groups", tags=["access-groups"])


@router.post("/", response_model=AccessGroupInDB)
def create_access_group(access_group: AccessGroupCreate, db: Session = Depends(get_db)):
    """
    Create a new access group.
    """
    try:
        return access_group_service.create_access_group(db, access_group)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{access_group_id}", response_model=AccessGroupInDB)
def get_access_group(access_group_id: int, db: Session = Depends(get_db)):
    """
    Get an access group by ID.
    """
    db_access_group = access_group_service.get_access_group(db, access_group_id)
    if db_access_group is None:
        raise HTTPException(status_code=404, detail="Access group not found")
    return db_access_group


@router.get("/", response_model=List[AccessGroupInDB])
def get_access_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get a list of access groups with pagination.
    """
    return access_group_service.get_access_groups(db, skip=skip, limit=limit)


@router.put("/{access_group_id}", response_model=AccessGroupInDB)
def update_access_group(access_group_id: int, access_group: AccessGroupUpdate, db: Session = Depends(get_db)):
    """
    Update an access group by ID.
    """
    updated_access_group = access_group_service.update_access_group(db, access_group_id, access_group)
    if updated_access_group is None:
        raise HTTPException(status_code=404, detail="Access group not found")
    try:
        return updated_access_group
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{access_group_id}")
def delete_access_group(access_group_id: int, db: Session = Depends(get_db)):
    """
    Delete an access group by ID.
    """
    success = access_group_service.delete_access_group(db, access_group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Access group not found")
    return {"message": "Access group deleted successfully"}


@router.get("/name/{name}", response_model=AccessGroupInDB)
def get_access_group_by_name(name: str, db: Session = Depends(get_db)):
    """
    Get an access group by name.
    """
    db_access_group = access_group_service.get_access_group_by_name(db, name)
    if db_access_group is None:
        raise HTTPException(status_code=404, detail="Access group not found")
    return db_access_group


# for route in router.routes:
#     if isinstance(route, fastapi.routing.APIRoute):
#         # The condition is changed to check if 'GET' is NOT in the methods
#         if "GET" not in route.methods:
#             route.dependencies.append(Depends(require_group("Admin")))
