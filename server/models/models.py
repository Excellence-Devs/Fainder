from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    gender = Column(String)
    birth_date = Column(String)
    photo_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    swipes = relationship("Swipe", back_populates="user")
    messages = relationship("Message", back_populates="user")

class Swipe(Base):
    __tablename__ = "swipes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    character_id = Column(String, index=True) # ID from the JSON file
    is_like = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="swipes")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    character_id = Column(String, index=True)
    sender = Column(String) # "user" or "character"
    content = Column(Text)
    attachments = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="messages")
