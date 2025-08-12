# src/models/mongo_models.py (As Fichas e Receitas, agora com selo de qualidade Pydantic)

import os
import json # Importar a biblioteca JSON
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional, List, Any

# Importamos a classe de conexão para usar como "type hint"
from database.database import DatabaseConnection

# =================================================================
# CLASSE BASE COMUM (Inspirada no Guia)
# =================================================================

class MongoBaseModel(BaseModel):
    """
    Uma ficha de registro base com selo de qualidade Pydantic.
    Garante que todos os registros tenham um ID e possam ser convertidos para dicionário.
    """
    id: Optional[ObjectId] = Field(None, alias='_id')

    class Config:
        # Permite que o Pydantic funcione bem com os objetos do MongoDB
        populate_by_name = True
        arbitrary_types_allowed = True
        # CORREÇÃO 1: Adicionar um encoder para o tipo datetime
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> dict:
        """
        Converte a ficha (modelo) para um dicionário, garantindo que todos os campos
        sejam compatíveis com JSON (serializáveis).
        """
        # CORREÇÃO 2: Usar model_dump_json para aplicar os encoders
        # Isso converte ObjectId e datetime para strings de forma confiável.
        data_json_string = self.model_dump_json(by_alias=True)
        data = json.loads(data_json_string)
        
        if '_id' in data:
            data['id'] = data['_id']
            del data['_id']
        return data

# =================================================================
# MODELO DE USUÁRIO (Sua Classe + Pydantic)
# =================================================================

class MongoUser(MongoBaseModel):
    """A ficha de registro de um cliente, com validação de dados."""
    username: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    async def create_user(cls, db_manager: DatabaseConnection, username: str, password: str) -> Optional['MongoUser']:
        """Cria um novo usuário, usando o cofre e retornando uma ficha validada."""
        if db_manager.db is None:
            print("⚠️ Gerente indisponível, operação de criar usuário não realizada.")
            return None

        users_collection = db_manager.db.users
        if await users_collection.find_one({"username": username}):
            return None  # Usuário já existe
        
        user_data = {
            "username": username,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.utcnow()
        }
        
        result = await users_collection.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        return cls(**user_data) # Retorna uma instância da classe, não um dicionário

    @classmethod
    async def find_by_username(cls, db_manager: DatabaseConnection, username: str) -> Optional['MongoUser']:
        """Busca usuário e retorna uma ficha validada."""
        if db_manager.db is None: return None
        user_data = await db_manager.db.users.find_one({"username": username})
        return cls(**user_data) if user_data else None
    
    @classmethod
    async def find_by_id(cls, db_manager: DatabaseConnection, user_id: str) -> Optional['MongoUser']:
        """Busca usuário por ID e retorna uma ficha validada."""
        if db_manager.db is None: return None
        try:
            user_data = await db_manager.db.users.find_one({"_id": ObjectId(user_id)})
            return cls(**user_data) if user_data else None
        except Exception:
            return None # Retorna None se o ObjectId for inválido

    def check_password(self, password: str) -> bool:
        """Verifica a senha contra o hash na ficha."""
        return check_password_hash(self.password_hash, password)

# =================================================================
# MODELO DE MÚSICA (Sua Classe + Pydantic)
# =================================================================

class MongoMusic(MongoBaseModel):
    """A receita de uma música, com validação de ingredientes."""
    userId: str
    music_url: Optional[str] = None
    music_name: str
    description: str
    lyrics: Optional[str] = None
    voice_type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    timestamp: int

    @classmethod
    async def add_generated_music(cls, db_manager: DatabaseConnection, music_data: dict) -> Optional['MongoMusic']:
        """
        O Arquivista registra uma nova receita no livro, retornando uma ficha validada.
        (Seu método original, agora retornando um objeto Pydantic)
        """
        music_name_for_log = music_data.get('musicName', 'Sem título')
        print(f"✍️ Arquivista: Registrando o prato '{music_name_for_log}' no livro de receitas.")
        
        if db_manager.db is None:
            print("⚠️ Gerente indisponível, não foi possível registrar a música.")
            return None
        
        user_id = music_data.get("userId")
        if not user_id:
            print(f"❌ Arquivista: Tentativa de registrar um prato sem identificação do cliente. Registro cancelado.")
            return None

        try:
            music_doc = {
                "userId": user_id,
                "music_url": music_data.get("musicUrl"),
                "music_name": music_data.get("musicName", "Música Sem Título"),
                "description": music_data.get("description", ""),
                "lyrics": music_data.get("lyrics", ""),
                "voice_type": music_data.get("voiceType", "instrumental"),
                "created_at": datetime.utcnow(),
                "timestamp": music_data.get("timestamp", int(datetime.utcnow().timestamp()))
            }
            result = await db_manager.db.musics.insert_one(music_doc)
            music_doc["_id"] = result.inserted_id
            return cls(**music_doc) # Retorna uma instância da classe
        except Exception as error:
            print(f"🚨 Arquivista: Falha crítica ao tentar registrar o prato '{music_name_for_log}': {error}")
            return None

    @classmethod
    async def find_by_user(cls, db_manager: DatabaseConnection, user_id: str) -> List['MongoMusic']:
        """Busca todas as receitas de um cliente."""
        if db_manager.db is None: return []
        cursor = db_manager.db.musics.find({"userId": user_id}).sort("created_at", -1)
        music_list = await cursor.to_list(length=None)
        return [cls(**music) for music in music_list]

# =================================================================
# FUNÇÕES DE TOKEN (Sua lógica original, sem alterações)
# =================================================================

def generate_token(user_id: str) -> str:
    """Gera um crachá de acesso para o cliente."""
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, os.getenv('SECRET_KEY', 'alquimista-musical-secret-key-2024'), algorithm='HS256')

def verify_token(token: str) -> Optional[str]:
    """Verifica a validade de um crachá de acesso."""
    try:
        payload = jwt.decode(token, os.getenv('SECRET_KEY', 'alquimista-musical-secret-key-2024'), algorithms=['HS256'])
        return payload['user_id']
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
