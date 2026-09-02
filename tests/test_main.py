from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root():
  """Verifica que el endpoint de salud responda 200 OK."""
  response = client.get("/")
  assert response.status_code == 200
  assert response.json() == {
      "mensaje": "¡El servidor de Gestión de Certificados está vivo!"
  }


def test_upload_invalid_file_extension():
  """Verifica que rechace archivos que no sean PDF."""
  file_content = b"Contenido simulado de texto"
  files = {"file": ("test_doc.txt", file_content, "text/plain")}
  data = {"equipment_name": "Balanza 50kg", "client_name": "Empresa Test"}

  response = client.post("/upload-certificate/", data=data, files=files)

  assert response.status_code == 400
  assert (
      response.json()["detail"]
      == "Formato no permitido. Únicamente se aceptan archivos PDF."
  )