# src/routes/user.py (O Recepcionista)

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional
from pydantic import BaseModel, Field

# =================================================================
# CORREÇÃO APLICADA AQUI: De '..' para '.' ou, neste caso, sem pontos.
# =================================================================
from models.mongo_models import MongoUser, generate_token, verify_token

# --- Modelos Pydantic para Validação de Entrada ---
class UserCreate(BaseModel):
    username: str
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

# --- Router do FastAPI ---
user_router = APIRouter()

# --- Dependência para obter o ID do usuário a partir do token (O Crachá de Cliente) ---
async def get_current_user_id(authorization: Optional[str] = Header(None)):
    """Verifica o crachá (token) do cliente para dar acesso às áreas restritas."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Crachá de acesso (token Bearer) não encontrado na entrada.",
        )
    token = authorization.split(" ")[1]
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Crachá de acesso (token) inválido ou expirado. Por favor, faça o login novamente.",
        )
    return user_id

# --- Rotas do Recepcionista ---

@user_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Recepcionista registrando um novo cliente no livro de reservas."""
    print(f"🤵 Recepcionista: Recebendo um novo cliente para registro: '{user_data.username}'")
    try:
        user = MongoUser.create_user(user_data.username.strip(), user_data.password)
        if not user:
            print(f"⚠️ Recepcionista: Tentativa de registro com nome já existente: '{user_data.username}'")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este nome já consta em nosso livro de reservas. Por favor, escolha outro.",
            )
        
        token = generate_token(user["_id"])
        print(f"✅ Recepcionista: Cliente '{user_data.username}' registrado com sucesso. Entregando crachá de acesso.")
        
        return {
            "message": "Bem-vindo ao Alquimista Musical! Seu registro foi um sucesso.",
            "user": MongoUser.to_dict(user),
            "token": token,
        }
    except Exception as e:
        print(f"🚨 Recepcionista: Ocorreu um erro inesperado ao tentar registrar o cliente: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Houve um problema em nosso sistema de registro. Tente novamente.")

@user_router.post("/login")
async def login(user_data: UserLogin):
    """Recepcionista verificando a identidade de um cliente que está chegando."""
    print(f"🤵 Recepcionista: Cliente '{user_data.username}' está tentando entrar no restaurante.")
    try:
        user = MongoUser.find_by_username(user_data.username.strip())
        
        if not user or not MongoUser.check_password(user, user_data.password):
            print(f"🚫 Recepcionista: Acesso negado para '{user_data.username}'. Credenciais não conferem.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nome de usuário ou senha não conferem com nosso livro de reservas.",
            )
            
        token = generate_token(user["_id"])
        print(f"👍 Recepcionista: Cliente '{user_data.username}' verificado. Entregando novo crachá de acesso.")
        
        return {
            "message": "Login realizado com sucesso. Bom te ver de volta!",
            "user": MongoUser.to_dict(user),
            "token": token,
        }
    except Exception as e:
        print(f"🚨 Recepcionista: Ocorreu um erro inesperado durante o login: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Houve um problema em nosso sistema de login. Tente novamente.")

@user_router.get("/profile")
async def get_profile(current_user_id: str = Depends(get_current_user_id)):
    """Recepcionista buscando os dados do cliente no livro de reservas."""
    print(f"🤵 Recepcionista: Buscando informações do cliente com ID: {current_user_id}")
    try:
        user = MongoUser.find_by_id(current_user_id)
        if not user:
            print(f"❓ Recepcionista: Cliente com ID {current_user_id} não encontrado no livro de reservas.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não encontramos seus dados em nosso sistema.")
        
        print(f"✅ Recepcionista: Informações do cliente {user['username']} encontradas.")
        return {"user": MongoUser.to_dict(user)}
    except Exception as e:
        print(f"🚨 Recepcionista: Erro ao buscar informações do cliente: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Houve um problema ao buscar suas informações.")

@user_router.get("/users", include_in_schema=False)
async def get_users():
    """Recepcionista informando que a lista de todos os clientes é confidencial."""
    print("🔐 Recepcionista: Tentativa de acesso à lista completa de clientes foi bloqueada por segurança.")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A lista de todos os clientes é confidencial e não pode ser acessada.")
