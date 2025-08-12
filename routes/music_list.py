# src/routes/music_list.py (O Maître, agora com memória de curto prazo)

from fastapi import APIRouter, HTTPException, status, Depends, Request
from .user import get_current_user_id 
from models.mongo_models import MongoMusic
from database.database import get_database, DatabaseConnection
# 1. IMPORTAMOS O GERENTE DO BUFFET
from services.cache_service import CacheService

# --- Router do FastAPI ---
music_list_router = APIRouter()

# --- Rotas do Maître ---

# Esta rota parece ser para acesso público ou de admin, vamos mantê-la sem cache por enquanto.
@music_list_router.get("/musics/{user_id}")
async def get_user_musics(user_id: str, db_manager: DatabaseConnection = Depends(get_database)):
    """Maître buscando o cardápio pessoal de um cliente específico (geralmente para visualização pública)."""
    print(f"🤵 Maître: Consultando o cardápio pessoal do cliente {user_id} no livro de receitas.")
    try:
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
    db_manager: DatabaseConnection = Depends(get_database),
    # 2. O Maître agora trabalha em conjunto com o Gerente do Buffet
    cache_service: CacheService = Depends()
):
    """Maître buscando pratos no cardápio para o cliente, usando o Buffet para pedidos comuns."""
    query_params = request.query_params
    
    # 3. NOVA LÓGICA DE CACHE: Só usamos o Buffet se o cliente não pedir nada de especial (sem filtros)
    if not query_params:
        print(f"🤵 Maître: Cliente {current_user_id} pediu seu cardápio completo. Verificando o Buffet primeiro...")
        cached_music_list = await cache_service.get_user_music_list(current_user_id)
        if cached_music_list is not None:
            # O log agora reflete o HIT do cache!
            print(f"✅ Maître: Cardápio completo do cliente {current_user_id} servido diretamente do Buffet. Rápido e prático!")
            return {
                "status": "success",
                "source": "cache", # Adicionamos uma fonte para depuração
                "musics": cached_music_list,
                "total": len(cached_music_list),
            }
        print("🤵 Maître: Cardápio não estava no Buffet. Indo ao livro de receitas (MongoDB)...")

    # --- O fluxo normal continua se houver filtros ou se o cache falhar ---
    try:
        search_filter = {"userId": current_user_id}
        
        if query_params:
            print(f"🤵 Maître: Cliente {current_user_id} pediu para ver o cardápio com preferências especiais: {dict(query_params)}")
            for key, value in query_params.items():
                values = query_params.getlist(key)
                if len(values) > 1:
                    search_filter[key] = {"$in": values}
                elif len(values) == 1:
                    search_filter[key] = values[0]
            print(f"🔍 Maître: Buscando no livro de receitas com os filtros: {search_filter}")
        
        if db_manager.db is None:
            print("🚨 Maître: O livro de receitas (banco de dados) está inacessível no momento!")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Nosso livro de receitas está temporariamente indisponível.")
            
        cursor = db_manager.db.musics.find(search_filter)
        musics = await cursor.to_list(length=None)
        
        music_list = [MongoMusic.to_dict(music) for music in musics]
        print(f"✅ Maître: Encontramos {len(music_list)} pratos no livro de receitas que correspondem às preferências do cliente.")
        
        # 4. Se não havia filtros, agora colocamos o resultado no Buffet para a próxima vez
        if not query_params:
            await cache_service.set_user_music_list(current_user_id, music_list)
            print(f"👨‍🍳 Maître avisou o Buffet: O cardápio completo do cliente {current_user_id} foi atualizado para acesso rápido.")

        return {
            "status": "success",
            "source": "database",
            "filters_applied": search_filter if query_params else "none",
            "musics": music_list,
            "total": len(music_list),
        }
    except Exception as e:
        print(f"🚨 Maître: Houve um problema ao tentar filtrar o cardápio para o cliente {current_user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Houve um problema ao buscar os pratos em nosso cardápio.")
