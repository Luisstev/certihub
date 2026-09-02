import uuid
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from config import settings
from database import Base, engine, get_db
from models import CertificateModel
from schemas import CertificateResponse

# Inicializar tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API - Gestión de Certificados",
    description="Sistema backend para el almacenamiento y registro de certificados de calibración",
    version="1.0.0",
)

s3_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
)

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@app.get("/")
def read_root():
  return {"mensaje": "¡El servidor de Gestión de Certificados está vivo!"}


@app.post(
    "/upload-certificate/",
    response_model=CertificateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_certificate(
    equipment_name: str = Form(..., description="Nombre/Modelo del equipo"),
    client_name: str = Form(..., description="Nombre del cliente/empresa"),
    file: UploadFile = File(..., description="Archivo PDF del certificado"),
    db: Session = Depends(get_db),
):
  # 1. Validación de extensión de archivo
  if not file.filename.lower().endswith(".pdf"):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Formato no permitido. Únicamente se aceptan archivos PDF.",
    )

  # 2. Validación de tamaño máximo del archivo
  file.file.seek(0, 2)
  file_size = file.file.tell()
  file.file.seek(0)

  if file_size > MAX_FILE_SIZE_BYTES:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"El archivo excede el tamaño máximo permitido de {MAX_FILE_SIZE_MB} MB.",
    )

  # 3. Generar clave única para almacenamiento S3
  file_extension = file.filename.split(".")[-1]
  unique_s3_key = f"{uuid.uuid4()}.{file_extension}"

  # 4. Intento de subida a MinIO
  try:
    s3_client.upload_fileobj(
        file.file,
        settings.bucket_name,
        unique_s3_key,
        ExtraArgs={"ContentType": "application/pdf"},
    )
  except (BotoCoreError, ClientError) as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error al subir el archivo a MinIO: {str(e)}",
    )

  # 5. Intento de registro en SQL Server (con Rollback Físico en caso de fallo)
  db_certificate = CertificateModel(
      filename=file.filename,
      s3_key=unique_s3_key,
      equipment_name=equipment_name,
      client_name=client_name,
  )

  try:
    db.add(db_certificate)
    db.commit()
    db.refresh(db_certificate)
  except Exception as e:
    db.rollback()

    # Rollback Físico: Borrar de MinIO el archivo subido al fallar la persistencia relacional
    try:
      s3_client.delete_object(
          Bucket=settings.bucket_name, Key=unique_s3_key
      )
    except Exception as s3_err:
      print(f"Error secundario en rollback de MinIO: {s3_err}")

  return db_certificate


@app.get("/certificates/", response_model=list[CertificateResponse])
def list_certificates(db: Session = Depends(get_db)):
  return db.query(CertificateModel).all()


@app.get("/certificates/{certificate_id}/download")
def get_certificate_download_url(
    certificate_id: int, db: Session = Depends(get_db)
):
  cert = (
      db.query(CertificateModel)
      .filter(CertificateModel.id == certificate_id)
      .first()
  )
  if not cert:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="El certificado solicitado no existe.",
    )

  try:
    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.bucket_name, "Key": cert.s3_key},
        ExpiresIn=3600,
    )
  except (BotoCoreError, ClientError) as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error al generar enlace seguro: {str(e)}",
    )

  return {
      "certificate_id": cert.id,
      "filename": cert.filename,
      "download_url": presigned_url,
  }


@app.delete("/certificates/{certificate_id}", status_code=status.HTTP_200_OK)
def delete_certificate(certificate_id: int, db: Session = Depends(get_db)):
  cert = (
      db.query(CertificateModel)
      .filter(CertificateModel.id == certificate_id)
      .first()
  )
  if not cert:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="El certificado solicitado no existe.",
    )

  try:
    s3_client.delete_object(Bucket=settings.bucket_name, Key=cert.s3_key)
  except (BotoCoreError, ClientError) as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error al eliminar el archivo físico en MinIO: {str(e)}",
    )

  try:
    db.delete(cert)
    db.commit()
  except Exception as e:
    db.rollback()
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error al eliminar el registro en la base de datos: {str(e)}",
    )

  return {
      "mensaje": (
          f"Certificado con ID {certificate_id} eliminado exitosamente de MinIO"
          " y SQL Server."
      )
  }