# src/routes/music_list.py

from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List, Optional
from ..models.mongo_models import MongoMusic
from .user import get_current_user_id

# --- Router do FastAPI ---
music_list_router = APIRouter()

# --- Rotas ---

@music_list_router.get("/musics/{user_id}")
async def get_user_musics(user_id: str):
    """Endpoint para listar músicas de um usuário específico (sem filtros)"""
    try:
        musics = await MongoMusic.find_by_user(user_id)
        music_list = [MongoMusic.to_dict(music) for music in musics]
        
        return {
            "status": "success",
            "musics": music_list,
            "total": len(music_list),
        }
    except Exception as e:
        print(f"Erro ao buscar músicas do usuário {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor")

# =================================================================
# CORREÇÃO PRINCIPAL APLICADA AQUI
# A rota agora aceita filtros dinâmicos da URL
# =================================================================
@music_list_router.get("/musics")
async def get_my_musics_with_filters(
    request: Request, 
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Endpoint para listar as músicas do usuário autenticado, com suporte a filtros dinâmicos.
    Exemplo de uso: /musics?genre=samba&genre=rock&voiceType=male
    """
    try:
        # Começamos com o filtro obrigatório: o ID do usuário logado
        search_filter = {"userId": current_user_id}
        
        # Pegamos todos os parâmetros da URL
        query_params = request.query_params
        
        # Construímos o filtro dinamicamente
        for key, value in query_params.items():
            # getlist pega todos os valores para uma chave (ex: ?genre=a&genre=b)
            values = query_params.getlist(key)
            
            if len(values) > 1:
                # Se houver mais de um valor para o mesmo filtro, usamos o operador $in
                search_filter[key] = {"$in": values}
            elif len(values) == 1:
                # Se houver apenas um valor, fazemos uma busca direta
                search_filter[key] = values[0]
        
        print(f"🔍 Buscando músicas com o filtro: {search_filter}")
        
        # Usamos o filtro construído para buscar no banco de dados
        musics = await MongoMusic.find(search_filter).to_list()
        
        music_list = [MongoMusic.to_dict(music) for music in musics]
        
        return {
            "status": "success",
            "filters_applied": search_filter,
            "musics": music_list,
            "total": len(music_list),
        }
    except Exception as e:
        print(f"Erro ao buscar todas as músicas com filtros: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor")

def add_generated_music(music_data):
    """Função para adicionar música gerada à lista"""
    try:
        user_id = music_data.get("userId")
        if user_id:
            music = MongoMusic.create_music(user_id, music_data)
            print(f"✅ Música salva no MongoDB: {music_data.get('musicName', 'Sem título')}")
            return music
        else:
            print("❌ Erro: userId não fornecido para salvar música")
            return None
    except Exception as error:
        print(f"❌ Erro ao salvar música no MongoDB: {error}")
        return None
