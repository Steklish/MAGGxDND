from typing import Any, Generic, List, Optional, Type, TypeVar, Dict
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import as_declarative

# This assumes you have a Base class for your SQLAlchemy models
# from app.src.db.base_class import Base
@as_declarative()
class Base:
    def as_dict(self) -> Dict[str, Any]:
       return {c.name: getattr(self, c.name) for c in self.__table__.columns} # type: ignore


# Define custom types for our generic repository.
# This makes the code type-safe.
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        Base Repository with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        """
        self.model = model

    # --- READ METHODS ---

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get a single object by its primary key ID.
        """
        return db.query(self.model).filter(self.model.id == id).first() # type: ignore

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple objects with pagination.
        """
        return db.query(self.model).order_by(self.model.id).offset(skip).limit(limit).all() # type: ignore

    # --- CREATE, UPDATE, DELETE METHODS ---

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new object in the database.
        """
        # Convert Pydantic schema to a dictionary
        obj_in_data = obj_in.model_dump()
        # Create a SQLAlchemy model instance
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
        """
        Update an existing database object.
        """
        # Convert the existing DB object to a dictionary
        obj_data = db_obj.as_dict()
        # Get the update data from the input schema
        # `exclude_unset=True` ensures we only update the fields that were actually provided
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Overwrite the old values with the new ones
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """
        Remove an object from the database by its ID.
        """
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj