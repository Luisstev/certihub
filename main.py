import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, File, HTTPException, UploadFile, status

app = FastAPI(
    title="API - Gestión de Certificados",
    description="Sistema backend para el almacenamiento y registro de certificados de calibración",
    version="1.0.0",
)

# Configuración del cliente S3 para MinIO local
S3_ENDPOINT = "http://127.0.0.1:9000"
AWS_ACCESS_KEY_ID = "admin"
AWS_SECRET_ACCESS_KEY = "password123"
BUCKET_NAME = "certificados"

# Inicializar cliente de S3 con boto3
s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


@app.get("/")
def read_root():
  return {"mensaje": "¡El servidor de Gestión de Certificados está vivo!"}


@app.post("/upload-certificate/", status_code=status.HTTP_201_CREATED)
async def upload_certificate(file: UploadFile = File(...)):
  # Validar que el archivo sea un PDF
  if not file.filename.lower().endswith(".pdf"):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Formato no permitido. Únicamente se aceptan archivos PDF.",
    )

  try:
    # Subir el archivo directamente desde la memoria al bucket de MinIO
    s3_client.upload_fileobj(
        file.file,
        BUCKET_NAME,
        file.filename,
        ExtraArgs={"ContentType": "application/pdf"},
    )
    return {
        "mensaje": "Certificado subido con éxito a la infraestructura S3",
        "filename": file.filename,
        "bucket": BUCKET_NAME,
    }
  except (BotoCoreError, ClientError) as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error en la comunicación con el servidor S3: {str(e)}",
    )