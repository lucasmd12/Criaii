# src/routes/user.py

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional
from pydantic import BaseModel, Field

# Importando seus modelos e funções de token (vamos assumir que eles funcionam como antes)
from ..models.mongo_models import MongoUser, generate_token, verify_token

# --- Modelos Pydantic para Validação de Entrada ---
# Isso substitui a necessidade de fazer `request.get_json()` e validar campo por campo.
class UserCreate(BaseModel):
    username: str
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

# --- Router do FastAPI ---
user_router = APIRouter()

# --- Dependência para obter o ID do usuário a partir do token ---
# Uma função reutilizável para proteger rotas
async def get_current_user_id(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorização do tipo Bearer é necessário",
        )
    token = authorization.split(" ")[1]
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )
    return user_id

# --- Rotas Convertidas ---

@user_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Registra um novo usuário"""
    try:
        user = MongoUser.create_user(user_data.username.strip(), user_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username já está em uso",
            )
        
        token = generate_token(user["_id"])
        
        return {
            "message": "Usuário criado com sucesso",
            "user": MongoUser.to_dict(user),
            "token": token,
        }
    except Exception as e:
        print(f"Erro no registro: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor")

@user_router.post("/login")
async def login(user_data: UserLogin):
    """Faz login do usuário e retorna um token JWT"""
    try:
        user = MongoUser.find_by_username(user_data.username.strip())
        
        if not user or not MongoUser.check_password(user, user_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username ou senha incorretos",
            )
            
        token = generate_token(user["_id"])
        
        return {
            "message": "Login realizado com sucesso",
            "user": MongoUser.to_dict(user),
            "token": token,
        }
    except Exception as e:
        print(f"Erro no login: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor")

@user_router.get("/profile")
async def get_profile(current_user_id: str = Depends(get_current_user_id)):
    """Obtém perfil do usuário autenticado"""
    try:
        user = MongoUser.find_by_id(current_user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        
        return {"user": MongoUser.to_dict(user)}
    except Exception as e:
        print(f"Erro ao obter perfil: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor")

@user_router.get("/users", include_in_schema=False) # Oculta da documentação da API
async def get_users():
    """Lista todos os usuários (desabilitado por segurança)"""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Endpoint desabilitado por segurança")

