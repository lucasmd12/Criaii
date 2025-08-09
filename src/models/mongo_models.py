# src/models/mongo_models.py (As Receitas e os Clientes)

import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
from bson import ObjectId

# ================== INÍCIO DA CORREÇÃO ==================
# REMOVEMOS COMPLETAMENTE a lógica de conexão com o banco de dados daqui.
# Este arquivo não deve mais gerenciar a conexão. Ele apenas define
# como interagir com o banco de dados, uma vez que a conexão seja fornecida.
# A importação de DatabaseConnection foi removida para evitar ciclos.
# As anotações de tipo para db_manager também foram removidas para evitar
# a necessidade de importar DatabaseConnection aqui, quebrando o ciclo.
# =================== FIM DA CORREÇÃO ====================

class MongoUser:
    @staticmethod
    async def create_user(db_manager, username, password):
        """Cria um novo usuário, usando o cofre fornecido pelo Gerente."""
        if not db_manager.db:
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
    
    @staticmethod
    async def find_by_username(db_manager, username):
        """Busca usuário por username, usando o cofre fornecido pelo Gerente."""
        if not db_manager.db: 
            return None
        return await db_manager.db.users.find_one({"username": username})
    
    @staticmethod
    async def find_by_id(db_manager, user_id):
        """Busca usuário por ID, usando o cofre fornecido pelo Gerente."""
        if not db_manager.db: 
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
    @staticmethod
    async def create_music(db_manager, user_id, music_data):
        """Cria uma nova música, registrando no cofre fornecido pelo Gerente."""
        if not db_manager.db:
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
    
    @staticmethod
    async def find_by_user(db_manager, user_id):
        """Busca músicas de um usuário, usando o cofre fornecido pelo Gerente."""
        if not db_manager.db: 
            return []
        cursor = db_manager.db.musics.find({"userId": user_id}).sort("created_at", -1)
        return await cursor.to_list(length=None)
    
    @staticmethod
    async def find_all(db_manager):
        """Busca todas as músicas, usando o cofre fornecido pelo Gerente."""
        if not db_manager.db: 
            return []
        cursor = db_manager.db.musics.find().sort("created_at", -1)
        return await cursor.to_list(length=None)
    
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
    """Gera token JWT para o usuário"""
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, os.getenv('SECRET_KEY', 'alquimista-musical-secret-key-2024'), algorithm='HS256')

def verify_token(token):
    """Verifica se o token JWT é válido"""
    try:
        payload = jwt.decode(token, os.getenv('SECRET_KEY', 'alquimista-musical-secret-key-2024'), algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

