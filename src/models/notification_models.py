# src/models/notification_models.py

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bson import ObjectId

# ================== INÍCIO DA CORREÇÃO ==================
# REMOVEMOS a importação do MongoClient.
# from pymongo import MongoClient

# Importamos a classe do nosso Gerente para checagem de tipo.
from database import DatabaseConnection
# =================== FIM DA CORREÇÃO ====================

class NotificationService:
    """Serviço para gerenciar notificações e histórico de processos, usando a conexão fornecida."""
    
    # O __init__ agora não faz nada, pois a conexão é gerenciada externamente.
    def __init__(self):
        print("✅ Serviço de Notificação pronto para operar com o Gerente do Cofre.")

    async def save_process_history(self, db_manager: DatabaseConnection, user_id: str, process_id: str, step: str, status: str, message: str):
        """Salva cada etapa do processo para histórico."""
        if not db_manager.db: return
        
        try:
            process_step = {
                "status": status,
                "message": message,
                "step": step,
                "timestamp": datetime.utcnow(),
            }
            
            await db_manager.db.process_history.update_one(
                {"user_id": user_id, "process_id": process_id},
                {"$set": process_step, "$setOnInsert": {"user_id": user_id, "process_id": process_id}},
                upsert=True
            )
            print(f"📝 Histórico de processo '{process_id}' atualizado: {step}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar etapa do processo: {e}")
    
    async def create_notification(self, db_manager: DatabaseConnection, user_id: str, title: str, message: str, notification_type: str, metadata: dict):
        """Salva notificação para visualização offline."""
        if not db_manager.db: return None
            
        try:
            notification = {
                "user_id": user_id,
                "type": notification_type,
                "title": title,
                "message": message,
                "metadata": metadata,
                "timestamp": datetime.utcnow(),
                "read": False,
            }
            
            result = await db_manager.db.notifications.insert_one(notification)
            print(f"🔔 Notificação salva para {user_id}: {title}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Erro ao salvar notificação: {e}")
            return None
    
    async def get_user_notifications(self, db_manager: DatabaseConnection, user_id: str, limit: int = 50, skip: int = 0) -> List[Dict]:
        """Recupera notificações do usuário."""
        if not db_manager.db: return []
            
        try:
            cursor = db_manager.db.notifications.find({"user_id": user_id}).sort("timestamp", -1).skip(skip).limit(limit)
            notifications = await cursor.to_list(length=limit)
            
            for n in notifications:
                n["id"] = str(n.pop("_id"))
                n["timestamp"] = n["timestamp"].isoformat()
            
            return notifications
            
        except Exception as e:
            print(f"❌ Erro ao recuperar notificações: {e}")
            return []
    
    async def get_process_history(self, db_manager: DatabaseConnection, user_id: str, limit: int = 20, skip: int = 0) -> List[Dict]:
        """Recupera histórico de processos do usuário."""
        if not db_manager.db: return []
            
        try:
            cursor = db_manager.db.process_history.find({"user_id": user_id}).sort("timestamp", -1).skip(skip).limit(limit)
            history = await cursor.to_list(length=limit)
            
            for record in history:
                record["id"] = str(record.pop("_id"))
                record["timestamp"] = record["timestamp"].isoformat()
            
            return history
            
        except Exception as e:
            print(f"❌ Erro ao recuperar histórico: {e}")
            return []
    
    async def mark_notifications_as_read(self, db_manager: DatabaseConnection, user_id: str, notification_ids: List[str] = None):
        """Marca notificações como lidas."""
        if not db_manager.db: return 0
            
        try:
            query = {"user_id": user_id, "read": False}
            if notification_ids:
                query["_id"] = {"$in": [ObjectId(nid) for nid in notification_ids]}
            
            result = await db_manager.db.notifications.update_many(query, {"$set": {"read": True}})
            
            print(f"✅ {result.modified_count} notificações marcadas como lidas para {user_id}")
            return result.modified_count
            
        except Exception as e:
            print(f"❌ Erro ao marcar notificações como lidas: {e}")
            return 0
    
    async def get_unread_count(self, db_manager: DatabaseConnection, user_id: str) -> int:
        """Retorna quantidade de notificações não lidas."""
        if not db_manager.db: return 0
            
        try:
            count = await db_manager.db.notifications.count_documents({"user_id": user_id, "read": False})
            return count
        except Exception as e:
            print(f"❌ Erro ao contar notificações não lidas: {e}")
            return 0

# ================== INÍCIO DA CORREÇÃO ==================
# A instância global continua, mas agora ela é "burra", não cria mais uma conexão.
# Ela apenas espera que o db_manager seja passado para seus métodos.
notification_service = NotificationService()
# =================== FIM DA CORREÇÃO ====================
