from sqlalchemy import Column, Integer, Text, DateTime, LargeBinary, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Card(Base):
    __tablename__ = "cards"

    id          = Column(Integer, primary_key=True)
    name        = Column(Text)
    designation = Column(Text)
    company     = Column(Text)
    country     = Column(Text)
    phone       = Column(Text)
    email       = Column(Text)
    address     = Column(Text)
    full_text   = Column(Text)
    image_path  = Column(Text, unique=True)
    embedding   = Column(LargeBinary, nullable=False)  # Store as binary (numpy array bytes)
    created_at  = Column(DateTime, server_default=func.now())
