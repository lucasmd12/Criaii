# src/routes/music_list.py

from fastapi import APIRouter, HTTPException, status, Depends
# CORREÇÃO: Importação relativa para funcionar com a estrutura do src/
from .user import get_current_user_id 
from ..models.mongo_models import MongoMusic

# --- Router do FastAPI ---
music_list_router = APIRouter()

# --- Rotas Convertidas ---

@music_list_router.get("/musics/{user_id}")
async def get_user_musics(user_id: str):
    """Endpoint para listar músicas de um usuário específico"""
    try:
        # ===== CORREÇÃO PRINCIPAL APLICADA AQUI =====
        musics = await MongoMusic.find_by_user(user_id)
        # ============================================
        
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
async def get_my_musics(current_user_id: str = Depends(get_current_user_id)):
    """Endpoint para listar as músicas do usuário autenticado"""
    try:
        # ===== CORREÇÃO PRINCIPAL APLICADA AQUI =====
        musics = await MongoMusic.find_by_user(current_user_id)
        # ============================================
        
        music_list = [MongoMusic.to_dict(music) for music in musics]
        
        return {
            "status": "success",
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
            # Se create_music também for assíncrono, precisará de 'await' quando for chamado em uma função async
            music = MongoMusic.create_music(user_id, music_data)
            print(f"✅ Música salva no MongoDB: {music_data.get('musicName', 'Sem título')}")
            return music
        else:
            print("❌ Erro: userId não fornecido para salvar música")
            return None
    except Exception as error:
        print(f"❌ Erro ao salvar música no MongoDB: {error}")
        return None

