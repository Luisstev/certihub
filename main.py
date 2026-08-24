import boto3
from botocore.exceptions import BotoCoreError, ClientError
from config import settings
from fastapi import FastAPI, File, HTTPException, UploadFile, status

app = FastAPI(
    title="API - Gestión de Certificados",
    description="Sistema backend para el almacenamiento y registro de certificados de calibración",
    version="1.0.0",
)

# Inicializar cliente de S3 leyendo las variables desde settings
s3_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
)


@app.get("/")
def read_root():
  return {"mensaje": "¡El servidor de Gestión de Certificados está vivo!"}


@app.post("/upload-certificate/", status_code=status.HTTP_201_CREATED)
async def upload_certificate(file: UploadFile = File(...)):
  if not file.filename.lower().endswith(".pdf"):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Formato no permitido. Únicamente se aceptan archivos PDF.",
    )

  try:
    s3_client.upload_fileobj(
        file.file,
        settings.bucket_name,
        file.filename,
        ExtraArgs={"ContentType": "application/pdf"},
    )
    return {
        "mensaje": "Certificado subido con éxito a la infraestructura S3",
        "filename": file.filename,
        "bucket": settings.bucket_name,
    }
  except (BotoCoreError, ClientError) as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error en la comunicación con el servidor S3: {str(e)}",
    )