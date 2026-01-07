import email
import logging

from tkinter import NO
from uuid import UUID as pyUUID
from datetime import datetime
from typing import Optional
from open_knowledge.env import SRC_LOG_LEVELS
from open_knowledge.internal.db import Base, JSONField, get_db

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Column,
    Date,
    String,
    Text,
    DateTime,
    UUID,
    true
)
from sqlalchemy.orm import relationship


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])


####################
# User DB Schema
####################


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String)
    last_sign_in_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)

    # relationship to UserInfo
    user_info = relationship(
        "UserInfo", back_populates="user", lazy="joined", uselist=False)


class UserInfo(Base):
    __tablename__ = "user_info"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=False)
    role = Column(String)
    profile_image_url = Column(Text)
    gender = Column(String)
    date_of_birth = Column(Date)
    info = Column(JSONField)
    settings = Column(JSONField)
    user_id = Column(UUID(as_uuid=true), ForeignKey("auth.users.id"))
    user = relationship("User", back_populates="user_info", uselist=False)


class UserSettings(BaseModel):
    ui: Optional[dict] = {}
    model_config = ConfigDict(extra="allow")


class UserInfoModel(BaseModel):
    id: int
    username: str
    role: str = "pending"
    profile_image_url: str | None = None
    gender: str | None = None
    date_of_birth: datetime | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    settings: Optional[UserSettings] = None
    info: Optional[dict] = None

    user_id: pyUUID

    model_config = ConfigDict(
        from_attributes=True,       # Allows mapping from SQLAlchemy objects
        extra="ignore",             # Silentily drop fields not defined here
        str_strip_whitespace=True,  # "  Phone. " becomes "Phone."
    )


class UserModel(BaseModel):
    id: pyUUID
    email: str

    last_sign_in_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    user_info: Optional[UserInfoModel] = None

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class UserResponse(BaseModel):
    id: pyUUID
    email: str
    user_info: UserInfoModel | None = None


class UserRoleUpdateForm(BaseModel):
    id: pyUUID
    role: str


class UserInfoUpdateForm(BaseModel):
    role: str
    username: str
    email: str
    profile_image_url: str


class UsersTable:

    def upsert_user_info(
        self,
        user_id: str,
        username: str,
        gender: str,
        profile_image_url: str,
        date_of_birth: str,
        role: str
    ) -> Optional[UserInfo]:
        with get_db() as db:
            user_info = db.query(UserInfo).filter_by(user_id=user_id).first()

            upsert_dict = UserInfoModel(**{
                "user_id": user_id,
                "username": username,
                "gender": gender,
                "profile_image_url": profile_image_url,
                "role": role,
                "date_of_birth": date_of_birth
            }).model_dump()

            if user_info is None:
                # Create a new user_info, which is related to the given user_id
                result = UserInfo(**upsert_dict)
                db.add(result)
                db.commit()
                db.refresh(result)
                if result:
                    return user_info
                else:
                    return None
            else:
                # Update the existing user_info
                for field, value in upsert_dict:
                    setattr(user_info, field, value)
                db.commit()

    def get_user_by_id(self, id: str) -> Optional[UserModel]:
        try:
            with get_db() as db:
                user = db.query(User).filter_by(id=id).first()
                return UserModel.model_validate(user)
        except Exception as e:
            log.error(f"Failed to fetch the user {id}: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[UserModel]:
        try:
            with get_db() as db:
                user = db.query(User).filter_by(email=email).first()
                return UserModel.model_validate(user)
        except Exception as e:
            log.error(f"Failed to fetch the user by email {email}: {e}")
            return None

    def update_user_role_by_id(self, id: str, role: str) -> Optional[UserModel]:
        try:
            with get_db() as db:
                db.query(UserInfo).filter_by(user_id=id).update({"role": role})
                db.commit()

                user = db.query(User).filter_by(id=id).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

    def update_user_profile_image_url_by_id(self, id: str, profile_image_url: str) -> Optional[UserModel]:
        try:
            with get_db() as db:
                db.query(UserInfo).filter_by(user_id=id).update(
                    {"profile_image_url": profile_image_url}
                )
                db.commit()

                user = db.query(User).filter_by(id=id).first()
                return UserModel.model_validate(user)
        except Exception:
            return None


Users = UsersTable()
