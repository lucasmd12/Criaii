import os
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import jwt

# Conexão com MongoDB
try:
    # Configuração SSL correta para MongoDB Atlas
    client = MongoClient(
        os.getenv('MONGO_URI'),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        tls=True,
        retryWrites=True,
        w='majority'
    )
    client.admin.command('ping')
    db = client.alquimista_musical
    print("✅ MongoDB Atlas conectado com sucesso!")
    mongo_available = True
except Exception as e:
    print(f"❌ Erro ao conectar MongoDB Atlas: {e}")
    print("🔄 Usando banco em memória como fallback...")
    db = None
    client = None
    mongo_available = False

# Collections
if mongo_available and db is not None:
    users_collection = db.users
    musics_collection = db.musics
else:
    # Fallback para listas em memória
    users_collection = []
    musics_collection = []

class MongoUser:
    @staticmethod
    def create_user(username, password):
        """Cria um novo usuário"""
        if mongo_available and db is not None:
            # MongoDB
            if users_collection.find_one({"username": username}):
                return None  # Usuário já existe
            
            user_data = {
                "username": username,
                "password_hash": generate_password_hash(password),
                "created_at": datetime.utcnow()
            }
            
            result = users_collection.insert_one(user_data)
            user_data["_id"] = result.inserted_id
            return user_data
        else:
            # Fallback em memória
            for user in users_collection:
                if user["username"] == username:
                    return None
            
            user_data = {
                "_id": f"user_{len(users_collection) + 1}",
                "username": username,
                "password_hash": generate_password_hash(password),
                "created_at": datetime.utcnow()
            }
            users_collection.append(user_data)
            return user_data
    
    @staticmethod
    def find_by_username(username):
        """Busca usuário por username"""
        if mongo_available and db is not None:
            return users_collection.find_one({"username": username})
        else:
            for user in users_collection:
                if user["username"] == username:
                    return user
            return None
    
    @staticmethod
    def find_by_id(user_id):
        """Busca usuário por ID"""
        if mongo_available and db is not None:
            from bson import ObjectId
            return users_collection.find_one({"_id": ObjectId(user_id)})
        else:
            for user in users_collection:
                if str(user["_id"]) == str(user_id):
                    return user
            return None
    
    @staticmethod
    def check_password(user, password):
        """Verifica se a senha está correta"""
        return check_password_hash(user["password_hash"], password)
    
    @staticmethod
    def to_dict(user):
        """Converte usuário para dicionário"""
        if not user:
            return None
        return {
            "id": str(user["_id"]),
            "username": user["username"],
            "created_at": user["created_at"].isoformat() if user.get("created_at") else None
        }

class MongoMusic:
    @staticmethod
    def create_music(user_id, music_data):
        """Cria uma nova música"""
        if mongo_available and db is not None:
            # MongoDB
            music_doc = {
                "user_id": user_id,
                "music_url": music_data.get("musicUrl"),
                "music_name": music_data.get("musicName", "Música Sem Título"),
                "description": music_data.get("description", ""),
                "lyrics": music_data.get("lyrics", ""),
                "voice_type": music_data.get("voiceType", "instrumental"),
                "created_at": datetime.utcnow(),
                "timestamp": music_data.get("timestamp", int(datetime.utcnow().timestamp()))
            }
            
            result = musics_collection.insert_one(music_doc)
            music_doc["_id"] = result.inserted_id
            return music_doc
        else:
            # Fallback em memória
            music_doc = {
                "_id": f"music_{len(musics_collection) + 1}",
                "user_id": user_id,
                "music_url": music_data.get("musicUrl"),
                "music_name": music_data.get("musicName", "Música Sem Título"),
                "description": music_data.get("description", ""),
                "lyrics": music_data.get("lyrics", ""),
                "voice_type": music_data.get("voiceType", "instrumental"),
                "created_at": datetime.utcnow(),
                "timestamp": music_data.get("timestamp", int(datetime.utcnow().timestamp()))
            }
            musics_collection.append(music_doc)
            return music_doc
    
    @staticmethod
    def find_by_user(user_id):
        """Busca músicas de um usuário"""
        if mongo_available and db is not None:
            return list(musics_collection.find({"user_id": user_id}).sort("created_at", -1))
        else:
            user_musics = [music for music in musics_collection if music["user_id"] == user_id]
            return sorted(user_musics, key=lambda x: x["created_at"], reverse=True)
    
    @staticmethod
    def find_all():
        """Busca todas as músicas (para debug)"""
        if mongo_available and db is not None:
            return list(musics_collection.find().sort("created_at", -1))
        else:
            return sorted(musics_collection, key=lambda x: x["created_at"], reverse=True)
    
    @staticmethod
    def to_dict(music):
        """Converte música para dicionário"""
        if not music:
            return None
        return {
            "id": str(music["_id"]),
            "user_id": music["user_id"],
            "music_url": music["music_url"],
            "music_name": music["music_name"],
            "description": music["description"],
            "lyrics": music["lyrics"],
            "voice_type": music["voice_type"],
            "created_at": music["created_at"].isoformat() if music.get("created_at") else None,
            "timestamp": music["timestamp"]
        }

def generate_token(user_id):
    """Gera token JWT para o usuário"""
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow().timestamp() + (7 * 24 * 60 * 60)  # 7 dias
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

