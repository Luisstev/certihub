from fastapi import FastAPI

# Inicializamos la aplicación con información profesional para la documentación
app = FastAPI(
    title="API - Gestión de Certificados",
    description="Sistema backend para el almacenamiento y registro de certificados de calibración",
    version="1.0.0"
)

# Endpoint de prueba (Health Check)
@app.get("/")
def read_root():
    return {"mensaje": "¡El servidor de Gestión de Certificados está vivo!"}