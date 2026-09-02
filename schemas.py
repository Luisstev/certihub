from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CertificateResponse(BaseModel):
  id: int
  filename: str
  s3_key: str
  equipment_name: str
  client_name: str
  created_at: datetime

  model_config = ConfigDict(from_attributes=True)