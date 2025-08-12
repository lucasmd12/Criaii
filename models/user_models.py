# src/models/user_models.py (O Livro de Registros de Clientes)
# Autor: Projeto Alquimista Musical
# Versão: Migração completa para MongoDB - Seguindo a harmonia do projeto
# Descrição: Modelo de usuário para MongoDB, integrado com a arquitetura do estúdio musical, agora com validação Pydantic.

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Importa a classe de conexão com o banco de dados para tipagem e uso.
from database.database import DatabaseConnection
# Importa a classe base para herdar suas funcionalidades
from .mongo_models import MongoBaseModel

# =================================================================
# SUB-MODELOS PARA ESTRUTURAS ANINHADAS (Pydantic)
# =================================================================

class UserPreferences(BaseModel):
    """Preferências do cliente, agora com tipos definidos."""
    favorite_genres: List[str] = Field(default_factory=list)
    preferred_voice_type: str = "instrumental"
    notification_settings: Dict[str, bool] = Field(default_factory=lambda: {
        "email_notifications": True,
        "push_notifications": True,
        "music_completion": True,
        "process_updates": True
    })

class UserProfile(BaseModel):
    """Perfil do cliente, agora com tipos definidos."""
    display_name: str
    bio: str = ""
    avatar_url: str = ""
    preferences: UserPreferences = Field(default_factory=UserPreferences)

class UserStats(BaseModel):
    """Estatísticas do cliente, agora com tipos definidos."""
    total_musics_generated: int = 0
    total_time_in_studio: int = 0
    favorite_genre: Optional[str] = None
    last_activity: datetime = Field(default_factory=datetime.utcnow)

# =================================================================
# MODELO PRINCIPAL DE USUÁRIO (Sua Classe + Pydantic)
# =================================================================

class UserModel(MongoBaseModel):
    """
    🎭 O Livro de Registros de Clientes do Alquimista Musical
    
    Esta classe gerencia todos os aspectos relacionados aos usuários/clientes do estúdio,
    agora com a robustez e validação de dados do Pydantic.
    """
    username: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True
    profile: UserProfile
    stats: UserStats = Field(default_factory=UserStats)

    @classmethod
    async def create_user(cls, db_manager: DatabaseConnection, username: str, password: str, additional_data: dict = None):
        """🆕 Registra um novo cliente no livro de registros do estúdio."""
        if db_manager.db is None:
            print("⚠️ Livro de registros indisponível. Não foi possível registrar o novo cliente.")
            return None

        users_collection = db_manager.db.users
        
        if await users_collection.find_one({"username": username}):
            print(f"⚠️ Cliente '{username}' já está registrado no estúdio.")
            return None
        
        user_data = {
            "username": username,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.utcnow(),
            "last_login": None,
            "is_active": True,
            "profile": {
                "display_name": username,
                "bio": "",
                "avatar_url": "",
                "preferences": {
                    "favorite_genres": [],
                    "preferred_voice_type": "instrumental",
                    "notification_settings": {
                        "email_notifications": True,
                        "push_notifications": True,
                        "music_completion": True,
                        "process_updates": True
                    }
                }
            },
            "stats": {
                "total_musics_generated": 0,
                "total_time_in_studio": 0,
                "favorite_genre": None,
                "last_activity": datetime.utcnow()
            }
        }
        
        if additional_data:
            user_data.update(additional_data)
        
        try:
            # A validação Pydantic acontece aqui, antes de salvar
            validated_user = cls(**user_data)
            result = await users_collection.insert_one(validated_user.model_dump(by_alias=True))
            user_data["_id"] = result.inserted_id
            print(f"✅ Cliente '{username}' registrado com sucesso no estúdio. ID: {result.inserted_id}")
            return user_data
        except Exception as e:
            print(f"❌ Erro ao registrar cliente '{username}': {e}")
            return None
    
    @classmethod
    async def find_by_username(cls, db_manager: DatabaseConnection, username: str):
        """🔍 Busca um cliente pelo nome de usuário no livro de registros."""
        if db_manager.db is None: 
            print("⚠️ Livro de registros indisponível para consulta.")
            return None
        
        try:
            user = await db_manager.db.users.find_one({"username": username})
            if user:
                print(f"📖 Cliente '{username}' encontrado no livro de registros.")
            return user
        except Exception as e:
            print(f"❌ Erro ao buscar cliente '{username}': {e}")
            return None
    
    @classmethod
    async def find_by_id(cls, db_manager: DatabaseConnection, user_id: str):
        """🔍 Busca um cliente pelo ID no livro de registros."""
        if db_manager.db is None: 
            print("⚠️ Livro de registros indisponível para consulta.")
            return None
        
        try:
            user = await db_manager.db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                print(f"📖 Cliente com ID '{user_id}' encontrado no livro de registros.")
            return user
        except Exception as e:
            print(f"❌ Erro ao buscar cliente por ID '{user_id}': {e}")
            return None
    
    @classmethod
    async def update_last_login(cls, db_manager: DatabaseConnection, user_id: str):
        """🕐 Atualiza o último login do cliente."""
        if db_manager.db is None:
            return False
        
        try:
            result = await db_manager.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "last_login": datetime.utcnow(),
                        "stats.last_activity": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Erro ao atualizar último login: {e}")
            return False
    
    @classmethod
    async def update_music_stats(cls, db_manager: DatabaseConnection, user_id: str, genre: str = None):
        """📊 Atualiza as estatísticas de música do cliente."""
        if db_manager.db is None:
            return False
        
        try:
            update_data = {
                "$inc": {"stats.total_musics_generated": 1},
                "$set": {"stats.last_activity": datetime.utcnow()}
            }
            
            if genre:
                update_data["$set"]["stats.favorite_genre"] = genre
            
            result = await db_manager.db.users.update_one(
                {"_id": ObjectId(user_id)},
                update_data
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Erro ao atualizar estatísticas de música: {e}")
            return False
    
    @classmethod
    async def update_profile(cls, db_manager: DatabaseConnection, user_id: str, profile_data: dict):
        """👤 Atualiza o perfil do cliente."""
        if db_manager.db is None:
            return False
        
        try:
            update_fields = {}
            for key, value in profile_data.items():
                update_fields[f"profile.{key}"] = value
            
            result = await db_manager.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_fields}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Erro ao atualizar perfil: {e}")
            return False
    
    @staticmethod
    def check_password(user, password):
        """🔐 Verifica se a senha fornecida corresponde ao hash armazenado."""
        if not user or "password_hash" not in user:
            return False
        return check_password_hash(user["password_hash"], password)
    
    @staticmethod
    def to_dict(user):
        """📋 Converte o objeto do usuário do MongoDB para um dicionário Python."""
        if not user: 
            return None
        
        # Se o objeto já for uma instância do nosso modelo Pydantic, usa o método da instância
        if isinstance(user, cls):
            return user.model_dump(by_alias=True)

        # Se for um dicionário do banco, mantém a lógica original
        return {
            "id": str(user["_id"]),
            "username": user["username"],
            "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
            "last_login": user["last_login"].isoformat() if user.get("last_login") else None,
            "is_active": user.get("is_active", True),
            "profile": user.get("profile", {}),
            "stats": user.get("stats", {})
        }
    
    @staticmethod
    def to_public_dict(user):
        """🌐 Converte o usuário para um dicionário público (sem dados sensíveis)."""
        if not user:
            return None
        
        # Se o objeto já for uma instância do nosso modelo Pydantic, usa o método da instância
        if isinstance(user, cls):
            return {
                "id": str(user.id),
                "username": user.username,
                "display_name": user.profile.display_name,
                "bio": user.profile.bio,
                "avatar_url": user.profile.avatar_url,
                "total_musics": user.stats.total_musics_generated,
                "favorite_genre": user.stats.favorite_genre,
                "member_since": user.created_at.isoformat() if user.created_at else None
            }

        # Se for um dicionário do banco, mantém a lógica original
        return {
            "id": str(user["_id"]),
            "username": user["username"],
            "display_name": user.get("profile", {}).get("display_name", user["username"]),
            "bio": user.get("profile", {}).get("bio", ""),
            "avatar_url": user.get("profile", {}).get("avatar_url", ""),
            "total_musics": user.get("stats", {}).get("total_musics_generated", 0),
            "favorite_genre": user.get("stats", {}).get("favorite_genre"),
            "member_since": user["created_at"].isoformat() if user.get("created_at") else None
        }

# Nota: As funções generate_token e verify_token já estão definidas em /models/mongo_models.py
# e devem ser importadas de lá diretamente para evitar duplicação de código.
