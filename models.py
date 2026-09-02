from datetime import datetime
from database import Base
from sqlalchemy import Column, DateTime, Integer, String


class CertificateModel(Base):
  __tablename__ = "certificates"

  id = Column(Integer, primary_key=True, index=True)
  filename = Column(String(255), nullable=False)
  s3_key = Column(String(255), nullable=False, unique=True)
  equipment_name = Column(String(255), nullable=False)
  client_name = Column(String(255), nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow)