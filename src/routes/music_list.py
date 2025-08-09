# src/routes/music_list.py

from fastapi import APIRouter, HTTPException, status, Depends, Request
# CORREÇÃO: Importação relativa para funcionar com a estrutura do src/
from .user import get_current_user_id 
from ..models.mongo_models import MongoMusic
# =================================================================
# PASSO 1: Importar a INSTÂNCIA da conexão do nosso novo arquivo
# =================================================================
from ..database import db_connection

# --- Router do FastAPI ---
music_list_router = APIRouter()

# --- Rotas Convertidas ---

@music_list_router.get("/musics/{user_id}")
async def get_user_musics(user_id: str):
    """Endpoint para listar músicas de um usuário específico"""
    try:
        # ===== Este método personalizado parece funcionar, vamos mantê-lo =====
        musics = await MongoMusic.find_by_user(user_id)
        # =====================================================================
        
        music_list = [MongoMusic.to_dict(music) for music in musics]
        
        return {
            "status": "success",
            "musics": music_list,
            "total": len(music_list),
        }
    except Exception as e:
        print(f"Erro ao buscar músicas: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor")

@music_list_router.get("/musics")
async def get_my_musics(request: Request, current_user_id: str = Depends(get_current_user_id)):
    """Endpoint para listar as músicas do usuário autenticado com filtros"""
    try:
        # Começa com o filtro base do usuário logado
        search_filter = {"userId": current_user_id}
        
        # Constrói o filtro dinâmico a partir dos parâmetros da URL
        query_params = request.query_params
        for key, value in query_params.items():
            values = query_params.getlist(key)
            if len(values) > 1:
                search_filter[key] = {"$in": values}
            elif len(values) == 1:
                search_filter[key] = values[0]
        
        print(f"🔍 Buscando músicas com o filtro: {search_filter}")

        # =================================================================
        # PASSO 2: CORREÇÃO FINAL APLICADA AQUI
        # Usamos a conexão ativa 'db_connection.db' para fazer a busca
        # =================================================================
        if not db_connection.db:
            print("❌ Erro crítico: Tentativa de busca sem conexão com o banco de dados.")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Banco de dados não conectado.")
            
        # Acessa a coleção 'musics' através da conexão ativa
        cursor = db_connection.db.musics.find(search_filter)
        musics = await cursor.to_list(length=None) # 'length=None' para buscar todos os documentos
        
        music_list = [MongoMusic.to_dict(music) for music in musics]
        
        return {
            "status": "success",
            "filters_applied": search_filter,
            "musics": music_list,
            "total": len(music_list),
        }
    except Exception as e:
        print(f"Erro ao buscar todas as músicas: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor")

def add_generated_music(music_data):
    """Função para adicionar música gerada à lista"""
    try:
        user_id = music_data.get("userId")
        if user_id:
            # Este método parece funcionar, vamos mantê-lo
            music = MongoMusic.create_music(user_id, music_data)
            print(f"✅ Música salva no MongoDB: {music_data.get('musicName', 'Sem título')}")
            return music
        else:
            print("❌ Erro: userId não fornecido para salvar música")
            return None
    except Exception as error:
        print(f"❌ Erro ao salvar música no MongoDB: {error}")
        return None
