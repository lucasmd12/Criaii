# src/models/mongo_models.py (Versão Corrigida)

import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
from bson import ObjectId

# Importamos a classe de conexão para usar como "type hint" (dica de tipo).
from database.database import DatabaseConnection

class MongoUser:
    @classmethod
    async def create_user(cls, db_manager: DatabaseConnection, username: str, password: str):
        """Cria um novo usuário, usando o cofre fornecido pelo Gerente."""
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
        return user_data
    
    @classmethod
    async def find_by_username(cls, db_manager: DatabaseConnection, username: str):
        """Busca usuário por username, usando o cofre fornecido pelo Gerente."""
        if db_manager.db is None: 
            return None
        return await db_manager.db.users.find_one({"username": username})
    
    @classmethod
    async def find_by_id(cls, db_manager: DatabaseConnection, user_id: str):
        """Busca usuário por ID, usando o cofre fornecido pelo Gerente."""
        if db_manager.db is None: 
            return None
        return await db_manager.db.users.find_one({"_id": ObjectId(user_id)})
    
    @staticmethod
    def check_password(user, password):
        """Verifica se a senha está correta (não precisa de acesso ao DB)."""
        return check_password_hash(user["password_hash"], password)
    
    @staticmethod
    def to_dict(user):
        """Converte usuário para dicionário (não precisa de acesso ao DB)."""
        if not user: 
            return None
        return {
            "id": str(user["_id"]),
            "username": user["username"],
            "created_at": user["created_at"].isoformat() if user.get("created_at") else None
        }

class MongoMusic:
    @classmethod
    async def create_music(cls, db_manager: DatabaseConnection, user_id: str, music_data: dict):
        """Cria uma nova música, registrando no cofre fornecido pelo Gerente."""
        if db_manager.db is None:
            print("⚠️ Gerente indisponível, operação de criar música não realizada.")
            return None

        musics_collection = db_manager.db.musics
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
        
        result = await musics_collection.insert_one(music_doc)
        music_doc["_id"] = result.inserted_id
        return music_doc
    
    @classmethod
    async def find_by_user(cls, db_manager: DatabaseConnection, user_id: str):
        """Busca músicas de um usuário, usando o cofre fornecido pelo Gerente."""
        if db_manager.db is None: 
            return []
        cursor = db_manager.db.musics.find({"userId": user_id}).sort("created_at", -1)
        return await cursor.to_list(length=None)
    
    @classmethod
    async def find_all(cls, db_manager: DatabaseConnection):
        """Busca todas as músicas, usando o cofre fornecido pelo Gerente."""
        if db_manager.db is None: 
            return []
        cursor = db_manager.db.musics.find().sort("created_at", -1)
        return await cursor.to_list(length=None)
    
    # ================== INÍCIO DA CORREÇÃO ==================
    # A função do "Arquivista" foi movida para cá, seu lugar correto.
    # Agora é um método da classe MongoMusic, pois sua responsabilidade
    # é registrar uma nova música no banco de dados.
    @classmethod
    async def add_generated_music(cls, db_manager: DatabaseConnection, music_data: dict):
        """Registra uma nova música gerada no banco de dados."""
        music_name_for_log = music_data.get('musicName', 'Sem título')
        print(f"✍️ Arquivista: Registrando o prato '{music_name_for_log}' no livro de receitas.")
        
        if db_manager.db is None:
            print("⚠️ Gerente indisponível, não foi possível registrar a música.")
            return None
        
        # Reutiliza a lógica de 'create_music' para evitar duplicação de código.
        # Se 'create_music' já faz o que precisamos, podemos simplesmente chamá-la.
        # No entanto, para manter a lógica original, vamos recriá-la aqui.
        user_id = music_data.get("userId")
        if not user_id:
            print(f"❌ Arquivista: Tentativa de registrar um prato sem identificação do cliente. Registro cancelado.")
            return None

        try:
            # A lógica de criação do documento é a mesma de create_music
            return await cls.create_music(db_manager, user_id, music_data)
        except Exception as error:
            print(f"🚨 Arquivista: Falha crítica ao tentar registrar o prato '{music_name_for_log}': {error}")
            return None
    # =================== FIM DA CORREÇÃO ====================

    @staticmethod
    def to_dict(music):
        """Converte música para dicionário (não precisa de acesso ao DB)."""
        if not music: 
            return None
        return {
            "id": str(music["_id"]),
            "user_id": music.get("userId"),
            "music_url": music.get("music_url"),
            "music_name": music.get("music_name"),
            "description": music.get("description"),
            "lyrics": music.get("lyrics"),
            "voice_type": music.get("voice_type"),
            "created_at": music["created_at"].isoformat() if music.get("created_at") else None,
            "timestamp": music.get("timestamp")
        }

# As funções de token não dependem do banco de dados, então podem continuar como estão.
def generate_token(user_id):
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, os.getenv('SECRET_KEY', 'alquimista-musical-secret-key-2024'), algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, os.getenv('SECRET_KEY', 'alquimista-musical-secret-key-2024'), algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
