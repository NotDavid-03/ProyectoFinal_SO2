from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
import os

app = FastAPI(title="Log de Eventos - Robótica")

# Configuración de CORS para que el frontend pueda consultar la API sin bloqueos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexión a MongoDB (Usa variable de entorno para Docker, o localhost por defecto para pruebas locales)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["sistema_logs"]
collection = db["eventos"]

# Modelo de datos que se espera recibir del proyecto de robótica
class Evento(BaseModel):
    componente: str      # Ejemplo: "Sensor_Ultrasonico", "Servomotor"
    accion: str          # Ejemplo: "Obstaculo_Detectado", "Giro_90_Grados"
    datos: dict          # Datos asociados extra (ej: {"distancia": 15})

@app.get("/")
def inicio():
    return {"mensaje": "Servidor de Logs Activo"}

# 1. Endpoint POST: Recibe y registra los eventos del sistema robótico
@app.post("/api/eventos")
def registrar_evento(evento: Evento):
    try:
        documento = evento.model_dump()
        # Agrega automáticamente el timestamp exacto del servidor al recibir el log
        documento["timestamp"] = datetime.utcnow()
        
        resultado = collection.insert_one(documento)
        return {"status": "ok", "id_insertado": str(resultado.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar en la Base de Datos: {str(e)}")

# 2. Endpoint GET: Devuelve todos los logs ordenados del más reciente al más antiguo
@app.get("/api/eventos")
def obtener_eventos():
    try:
        eventos = []
        # Buscamos los logs y los ordenamos por fecha descendente
        for doc in collection.find().sort("timestamp", -1):
            eventos.append({
                "id": str(doc["_id"]),
                "componente": doc["componente"],
                "accion": doc["accion"],
                "datos": doc["datos"],
                "timestamp": doc["timestamp"].isoformat() if isinstance(doc["timestamp"], datetime) else doc["timestamp"]
            })
        return eventos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar la Base de Datos: {str(e)}")