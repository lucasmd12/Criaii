# src/routes/music_list.py (O Maître) - Versão Corrigida

from fastapi import APIRouter, HTTPException, status, Depends, Request
from .user import get_current_user_id 
from models.mongo_models import MongoMusic
# A forma correta de pedir acesso ao "Gerente do Cofre".
from database.database import get_database, DatabaseConnection

# --- Router do FastAPI ---
music_list_router = APIRouter()

# --- Rotas do Maître ---

@music_list_router.get("/musics/{user_id}")
async def get_user_musics(user_id: str, db_manager: DatabaseConnection = Depends(get_database)):
    """Maître buscando o cardápio pessoal de um cliente específico."""
    print(f"🤵 Maître: Consultando o cardápio pessoal do cliente {user_id}.")
    try:
        # Agora usamos o 'db_manager' que o FastAPI nos entregou.
        musics = await MongoMusic.find_by_user(db_manager, user_id)
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
    # O Maître agora pede acesso ao Gerente do Cofre diretamente ao FastAPI.
    db_manager: DatabaseConnection = Depends(get_database)
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

        # Verificação corrigida para usar 'is None'
        if db_manager.db is None:
            print("🚨 Maître: O livro de receitas (banco de dados) está inacessível no momento!")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Nosso livro de receitas está temporariamente indisponível.")
            
        # Usamos o 'db_manager' fornecido pelo Depends.
        cursor = db_manager.db.musics.find(search_filter)
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

# ================== INÍCIO DA CORREÇÃO ==================
# A função 'add_generated_music' foi removida deste arquivo.
# Sua responsabilidade, que é interagir com o banco de dados,
# foi movida para a camada de modelos (mongo_models.py),
# que é o seu lugar correto na arquitetura do projeto.
# Isso quebra a dependência circular.
# =================== FIM DA CORREÇÃO ====================
