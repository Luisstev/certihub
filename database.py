from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuración de conexión
SERVER = r".\SQLEXPRESS"  # Usa '.\SQLEXPRESS' o 'localhost\SQLEXPRESS'
DATABASE = "certihub_db"  # Asegúrate de que este nombre exista en SQL Server

# Cadena de conexión pyodbc con evasión de SSL
odbc_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"  # Indispensable para ODBC Driver 18
)

# Codificación de la cadena para SQLAlchemy
params = quote_plus(odbc_str)
DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={params}"

# Creación del engine y sesión
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency para FastAPI / Flask
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()