# src/routes/user.py (O Recepcionista, agora mais eficiente)

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional
from pydantic import BaseModel, Field

from models.mongo_models import MongoUser, generate_token, verify_token
from database.database import get_database, DatabaseConnection
# 1. IMPORTAMOS O NOVO FUNCIONÁRIO: O GERENTE DO BUFFET
from services.cache_service import CacheService 

# --- Modelos Pydantic (sem mudanças) ---
class UserCreate(BaseModel):
    username: str
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

# --- Router do FastAPI ---
user_router = APIRouter()

# --- Dependência para obter o ID do usuário (sem mudanças) ---
async def get_current_user_id(authorization: Optional[str] = Header(None)):
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

# --- Rotas do Recepcionista (Atualizadas) ---

@user_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate, 
    db_manager: DatabaseConnection = Depends(get_database),
    # 2. O Recepcionista agora conhece o Gerente do Buffet
    cache_service: CacheService = Depends() # FastAPI vai injetar a instância criada no main.py
):
    """Recepcionista registrando um novo cliente no livro de reservas."""
    username = user_data.username.strip()
    print(f"🤵 Recepcionista: Recebendo um novo cliente para registro: '{username}'")
    
    try:
        user = await MongoUser.create_user(db_manager, username, user_data.password)
        
        if not user:
            print(f"⚠️ Recepcionista: Tentativa de registro com nome já existente: '{username}'")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este nome já consta em nosso livro de reservas. Por favor, escolha outro.",
            )
        
        user_id_str = str(user["_id"])
        token = generate_token(user_id_str)
        user_dict = MongoUser.to_dict(user)
        
        # 3. AÇÃO PROATIVA: Colocar os dados do novo cliente diretamente no Buffet
        await cache_service.set_user_data(user_id_str, user_dict)
        print(f"👨‍🍳 Recepcionista avisou o Buffet: Dados do novo cliente '{username}' já estão disponíveis para acesso rápido.")
        
        print(f"✅ Recepcionista: Cliente '{username}' registrado com sucesso. Entregando crachá de acesso.")
        
        return {
            "message": "Bem-vindo ao Alquimista Musical! Seu registro foi um sucesso.",
            "user": user_dict,
            "token": token,
        }
    except Exception as e:
        print(f"🚨 Recepcionista: Ocorreu um erro inesperado ao tentar registrar o cliente: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Houve um problema em nosso sistema de registro. Tente novamente.")

@user_router.post("/login")
async def login(
    user_data: UserLogin, 
    db_manager: DatabaseConnection = Depends(get_database),
    cache_service: CacheService = Depends() # Injetando o CacheService
):
    """Recepcionista verificando a identidade de um cliente que está chegando."""
    username = user_data.username.strip()
    print(f"🤵 Recepcionista: Cliente '{username}' está tentando entrar no restaurante.")
    
    try:
        user = await MongoUser.find_by_username(db_manager, username)
        
        if not user or not MongoUser.check_password(user, user_data.password):
            print(f"🚫 Recepcionista: Acesso negado para '{username}'. Credenciais não conferem.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nome de usuário ou senha não conferem com nosso livro de reservas.",
            )
            
        user_id_str = str(user["_id"])
        token = generate_token(user_id_str)
        user_dict = MongoUser.to_dict(user)

        # 4. AÇÃO PROATIVA: Atualizar os dados do cliente no Buffet
        await cache_service.set_user_data(user_id_str, user_dict)
        print(f"👨‍🍳 Recepcionista avisou o Buffet: Dados do cliente '{username}' foram atualizados para acesso rápido.")

        print(f"👍 Recepcionista: Cliente '{username}' verificado. Entregando novo crachá de acesso.")
        
        return {
            "message": "Login realizado com sucesso. Bom te ver de volta!",
            "user": user_dict,
            "token": token,
        }
    except Exception as e:
        print(f"🚨 Recepcionista: Ocorreu um erro inesperado durante o login: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Houve um problema em nosso sistema de login. Tente novamente.")

@user_router.get("/profile")
async def get_profile(
    current_user_id: str = Depends(get_current_user_id),
    db_manager: DatabaseConnection = Depends(get_database),
    cache_service: CacheService = Depends() # Injetando o CacheService
):
    """Recepcionista buscando os dados do cliente, agora com mais eficiência."""
    print(f"🤵 Recepcionista: Buscando informações do cliente com ID: {current_user_id}")

    # 5. NOVA LÓGICA: Verificar o Buffet PRIMEIRO!
    cached_user = await cache_service.get_user_data(current_user_id)
    if cached_user:
        # O log agora reflete que os dados vieram do cache!
        print(f"✅ Recepcionista: Informações do cliente '{cached_user.get('username')}' encontradas no Buffet. Entrega imediata!")
        return {"user": cached_user}

    # Se não encontrou no Buffet, o fluxo normal continua...
    print("🤵 Recepcionista: Informações não estavam no Buffet. Indo até o cofre (MongoDB)...")
    try:
        user = await MongoUser.find_by_id(db_manager, current_user_id)
        
        if not user:
            print(f"❓ Recepcionista: Cliente com ID {current_user_id} não encontrado no livro de reservas.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não encontramos seus dados em nosso sistema.")
        
        user_dict = MongoUser.to_dict(user)
        username = user_dict.get('username', 'desconhecido')
        
        # 6. Colocar os dados no Buffet para a próxima vez
        await cache_service.set_user_data(current_user_id, user_dict)
        print(f"👨‍🍳 Recepcionista avisou o Buffet: Dados do cliente '{username}' agora estão disponíveis para acesso rápido.")
        
        print(f"✅ Recepcionista: Informações do cliente '{username}' encontradas no cofre.")
        
        return {"user": user_dict}
    except Exception as e:
        print(f"🚨 Recepcionista: Erro ao buscar informações do cliente no cofre: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Houve um problema ao buscar suas informações.")

# Rota de exemplo para o futuro, mostrando a invalidação
# @user_router.put("/profile")
# async def update_profile(..., cache_service: CacheService = Depends()):
#     # ... lógica para atualizar o usuário no DB ...
#     await cache_service.invalidate_user_data(current_user_id)
#     print(f"🧹 Recepcionista avisou o Buffet: Os dados antigos do cliente {current_user_id} foram jogados fora.")
#     # ...

@user_router.get("/users", include_in_schema=False)
async def get_users():
    """Recepcionista informando que a lista de todos os clientes é confidencial."""
    print("🔐 Recepcionista: Tentativa de acesso à lista completa de clientes foi bloqueada por segurança.")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A lista de todos os clientes é confidencial e não pode ser acessada.")

