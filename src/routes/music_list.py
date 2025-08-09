# src/routes/music_list.py (O Maître e Arquivista)

from fastapi import APIRouter, HTTPException, status, Depends, Request
from .user import get_current_user_id 
from models.mongo_models import MongoMusic
# ================== INÍCIO DA CORREÇÃO ==================
# REMOVEMOS a importação direta e problemática.
# from database import db_connection 

# ADICIONAMOS a forma correta de pedir acesso ao "Gerente do Cofre".
from database import get_database, DatabaseConnection
# =================== FIM DA CORREÇÃO ====================

# --- Router do FastAPI ---
music_list_router = APIRouter()

# --- Rotas do Maître ---

@music_list_router.get("/musics/{user_id}")
async def get_user_musics(user_id: str, db_manager: DatabaseConnection = Depends(get_database)):
    """Maître buscando o cardápio pessoal de um cliente específico."""
    print(f"🤵 Maître: Consultando o cardápio pessoal do cliente {user_id}.")
    try:
        # ================== INÍCIO DA CORREÇÃO ==================
        # Agora usamos o 'db_manager' que o FastAPI nos entregou.
        musics = await MongoMusic.find_by_user(db_manager, user_id)
        # =================== FIM DA CORREÇÃO ====================
        music_list = [MongoMusic.to_dict(music) for music in musics]
        print(f"✅ Maître: Encontrados {len(music_list)} pratos no cardápio do cliente {user_id}.")
        
        return {
            "status": "success",
            "musics": music_list,
            "total": len(music_list),
        }
    except Exception as e:
        print(f"🚨 Maître: Erro ao consultar o cardápio do cliente {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Houve um problema ao buscar o cardápio deste cliente.")

@music_list_router.get("/musics")
async def get_my_musics(
    request: Request, 
    current_user_id: str = Depends(get_current_user_id),
    # ================== INÍCIO DA CORREÇÃO ==================
    # O Maître agora pede acesso ao Gerente do Cofre diretamente ao FastAPI.
    db_manager: DatabaseConnection = Depends(get_database)
    # =================== FIM DA CORREÇÃO ====================
):
    """Maître buscando pratos no cardápio para o cliente, aplicando seus filtros e preferências."""
    try:
        search_filter = {"userId": current_user_id}
        
        query_params = request.query_params
        if query_params:
            print(f"🤵 Maître: Cliente {current_user_id} pediu para ver o cardápio com preferências especiais: {dict(query_params)}")
        else:
            print(f"🤵 Maître: Cliente {current_user_id} pediu para ver seu cardápio completo.")

        for key, value in query_params.items():
            values = query_params.getlist(key)
            if len(values) > 1:
                search_filter[key] = {"$in": values}
            elif len(values) == 1:
                search_filter[key] = values[0]
        
        print(f"🔍 Maître: Buscando no livro de receitas com os filtros: {search_filter}")

        # ================== INÍCIO DA CORREÇÃO ==================
        if not db_manager.db:
            print("🚨 Maître: O livro de receitas (banco de dados) está inacessível no momento!")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Nosso livro de receitas está temporariamente indisponível.")
            
        # Usamos o 'db_manager' fornecido pelo Depends.
        cursor = db_manager.db.musics.find(search_filter)
        # =================== FIM DA CORREÇÃO ====================
        musics = await cursor.to_list(length=None)
        
        music_list = [MongoMusic.to_dict(music) for music in musics]
        print(f"✅ Maître: Encontramos {len(music_list)} pratos que correspondem às preferências do cliente.")
        
        return {
            "status": "success",
            "filters_applied": search_filter,
            "musics": music_list,
            "total": len(music_list),
        }
    except Exception as e:
        print(f"🚨 Maître: Houve um problema ao tentar filtrar o cardápio para o cliente {current_user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Houve um problema ao buscar os pratos em nosso cardápio.")

# --- Função do Arquivista ---

# ================== INÍCIO DA CORREÇÃO ==================
# O Arquivista agora precisa saber com qual 'Gerente' falar.
# Passamos o 'db_manager' como um argumento.
async def add_generated_music(db_manager: DatabaseConnection, music_data: dict):
# =================== FIM DA CORREÇÃO ====================
    """Função para adicionar música gerada à lista"""
    music_name_for_log = music_data.get('musicName', 'Sem título')
    print(f"✍️ Arquivista: Recebendo um novo prato da cozinha para registrar: '{music_name_for_log}'.")
    try:
        user_id = music_data.get("userId")
        if user_id:
            # ================== INÍCIO DA CORREÇÃO ==================
            # Passamos o 'db_manager' para a função que cria a música.
            music = await MongoMusic.create_music(db_manager, user_id, music_data)
            # =================== FIM DA CORREÇÃO ====================
            print(f"✅ Arquivista: Prato '{music_name_for_log}' do cliente {user_id} foi registrado com sucesso no livro de receitas (MongoDB).")
            return music
        else:
            print(f"❌ Arquivista: Tentativa de registrar um prato sem identificação do cliente. Registro cancelado.")
            return None
    except Exception as error:
        print(f"🚨 Arquivista: Falha crítica ao tentar registrar o prato '{music_name_for_log}' no livro de receitas: {error}")
        return None
