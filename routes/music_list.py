# src/routes/music_list.py (O Maître, agora com memória de curto prazo e autoridade para remover pratos)

from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List

# --- CORREÇÃO CRÍTICA: Usar dependency injection em vez de importações diretas ---
from .user import get_current_user_id
from dependencies import get_db_manager, get_cache_service, get_sync_service

# --- Importações de CLASSE para Type Hinting ---
from models.mongo_models import MongoMusic
from database.database import DatabaseConnection
from services.cache_service import CacheService
from services.sync_service import SyncService

# --- Router do FastAPI ---
music_list_router = APIRouter()

# --- Rotas do Maître ---

@music_list_router.get("/musics")
async def get_my_musics(
    request: Request, 
    current_user_id: str = Depends(get_current_user_id),
    db_manager: DatabaseConnection = Depends(get_db_manager),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Maître buscando pratos no cardápio para o cliente, usando o Buffet para pedidos comuns."""
    query_params = request.query_params
    
    if not query_params:
        print(f"🤵 Maître: Cliente {current_user_id} pediu seu cardápio completo. Verificando o Buffet primeiro...")
        cached_music_list = await cache_service.get_user_music_list(current_user_id)
        if cached_music_list is not None:
            print(f"✅ Maître: Cardápio completo do cliente {current_user_id} servido diretamente do Buffet!")
            return {"status": "success", "source": "cache", "musics": cached_music_list, "total": len(cached_music_list)}
        print("🤵 Maître: Cardápio não estava no Buffet. Indo ao livro de receitas (MongoDB)...")

    try:
        search_filter = {"userId": current_user_id}
        if query_params:
            # ... (sua lógica de filtros permanece a mesma) ...
            print(f"🔍 Maître: Buscando no livro de receitas com os filtros: {search_filter}")
        
        musics = await MongoMusic.find_by_user(db_manager, current_user_id) # Assumindo que find_by_user pode lidar com filtros
        music_list = [MongoMusic.to_dict(music) for music in musics]
        
        print(f"✅ Maître: Encontramos {len(music_list)} pratos no livro de receitas.")
        
        if not query_params:
            await cache_service.set_user_music_list(current_user_id, music_list)
            print(f"👨‍🍳 Maître avisou o Buffet: O cardápio do cliente {current_user_id} foi atualizado.")

        return {"status": "success", "source": "database", "musics": music_list, "total": len(music_list)}
    except Exception as e:
        print(f"🚨 Maître: Houve um problema ao tentar filtrar o cardápio: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Houve um problema ao buscar os pratos.")

# ADICIONADO: A rota de deleção agora vive aqui, com o Maître.
@music_list_router.delete("/musics/{music_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_music(
    music_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db_manager: DatabaseConnection = Depends(get_db_manager),
    cache_service: CacheService = Depends(get_cache_service),
    sync_service: SyncService = Depends(get_sync_service)
):
    """Maître removendo um prato do cardápio a pedido do cliente."""
    print(f"🤵 Maître: Cliente {current_user_id} pediu para remover o prato {music_id} do cardápio.")
    
    music = await MongoMusic.find_by_id(db_manager, music_id)
    if not music:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prato não encontrado no cardápio.")
    
    if music.get("userId") != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este prato não pertence ao seu cardápio.")

    deleted_count = await MongoMusic.delete_by_id(db_manager, music_id)
    if deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Não foi possível remover o prato do cardápio.")

    # Invalida o cache da lista de músicas do usuário
    await cache_service.invalidate_user_music_list(current_user_id)
    print(f"🧹 Maître avisou o Buffet: 'O cardápio do cliente {current_user_id} mudou, jogue fora a versão antiga!'")

    # Publica o evento de deleção para o frontend
    await sync_service.publish_event(
        event_type="music_deleted",
        user_id=current_user_id,
        payload={"music_id": music_id}
    )
    print(f"📡 Maître anunciou no sistema: 'O prato {music_id} foi removido do cardápio do cliente {current_user_id}!'")
    
    return # Retorna 204 No Content
