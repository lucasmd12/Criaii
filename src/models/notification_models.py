from pymongo import MongoClient
import os
from datetime import datetime
from typing import Dict, List, Optional

class NotificationService:
    """Serviço para gerenciar notificações e histórico de processos."""
    
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI")
        if self.mongo_uri:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client.alquimista_musical
            self.notifications_collection = self.db.notifications
            self.process_history_collection = self.db.process_history
        else:
            print("⚠️ MONGO_URI não configurada. Notificações não serão persistidas.")
            self.client = None
    
    def save_process_step(self, user_id: str, process_id: str, step_data: Dict):
        """Salva cada etapa do processo para histórico."""
        if not self.client:
            return
            
        try:
            process_step = {
                "user_id": user_id,
                "process_id": process_id,
                "step": step_data.get("step"),
                "progress": step_data.get("progress"),
                "message": step_data.get("message"),
                "timestamp": datetime.utcnow(),
                "estimated_time": step_data.get("estimated_time"),
                "status": "in_progress" if step_data.get("progress", 0) < 100 else "completed"
            }
            
            self.process_history_collection.update_one(
                {"user_id": user_id, "process_id": process_id},
                {"$set": process_step},
                upsert=True
            )
            print(f"📝 Processo atualizado/salvo: {step_data.get("step")} - {step_data.get("progress")}%")
            
        except Exception as e:
            print(f"❌ Erro ao salvar etapa do processo: {e}")
    
    def save_notification(self, user_id: str, notification_data: Dict):
        """Salva notificação para visualização offline."""
        if not self.client:
            return
            
        try:
            notification = {
                "user_id": user_id,
                "type": notification_data.get("type", "info"),
                "title": notification_data.get("title", ""),
                "message": notification_data.get("message", ""),
                "data": notification_data.get("data", {}),
                "timestamp": datetime.utcnow(),
                "read": False,
                "process_id": notification_data.get("process_id")
            }
            
            result = self.notifications_collection.insert_one(notification)
            print(f"🔔 Notificação salva: {notification['title']}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Erro ao salvar notificação: {e}")
            return None
    
    async def get_user_notifications(self, user_id: str, limit: int = 50, skip: int = 0) -> List[Dict]:
        """Recupera notificações do usuário."""
        if not self.client:
            return []
            
        try:
            notifications = list(
                self.notifications_collection
                .find({"user_id": user_id})
                .sort("timestamp", -1)
                .skip(skip)
                .limit(limit)
            )
            
            # Converte ObjectId para string
            for notification in notifications:
                notification["_id"] = str(notification["_id"])
                notification["timestamp"] = notification["timestamp"].isoformat()
            
            return notifications
            
        except Exception as e:
            print(f"❌ Erro ao recuperar notificações: {e}")
            return []
    
    async def get_process_history(self, user_id: str, process_id: str = None, limit: int = 20, skip: int = 0) -> List[Dict]:
        """Recupera histórico de processos do usuário."""
        if not self.client:
            return []
            
        try:
            query = {"user_id": user_id}
            if process_id:
                query["process_id"] = process_id
            
            # Agrega para obter o último status de cada processo
            pipeline = [
                {"$match": query},
                {"$sort": {"timestamp": -1}},
                {"$group": {
                    "_id": "$process_id",
                    "latest_record": {"$first": "$$ROOT"}
                }},
                {"$replaceRoot": {"newRoot": "$latest_record"}},
                {"$sort": {"timestamp": -1}},
                {"$limit": limit},
                {"$skip": skip}
            ]
            
            history = list(self.process_history_collection.aggregate(pipeline))
            
            # Converte ObjectId para string e formata timestamp
            for record in history:
                record["_id"] = str(record["_id"])
                record["timestamp"] = record["timestamp"].isoformat()
            
            return history
            
        except Exception as e:
            print(f"❌ Erro ao recuperar histórico: {e}")
            return []
    
    async def mark_notifications_as_read(self, user_id: str, notification_ids: List[str] = None):
        """Marca notificações como lidas."""
        if not self.client:
            return
            
        try:
            query = {"user_id": user_id}
            if notification_ids:
                from bson import ObjectId
                query["_id"] = {"$in": [ObjectId(nid) for nid in notification_ids]}
            
            result = self.notifications_collection.update_many(
                query,
                {"$set": {"read": True}}
            )
            
            print(f"✅ {result.modified_count} notificações marcadas como lidas")
            return result.modified_count
            
        except Exception as e:
            print(f"❌ Erro ao marcar notificações como lidas: {e}")
            return 0
    
    async def get_unread_count(self, user_id: str) -> int:
        """Retorna quantidade de notificações não lidas."""
        if not self.client:
            return 0
            
        try:
            count = self.notifications_collection.count_documents({
                "user_id": user_id,
                "read": False
            })
            return count
            
        except Exception as e:
            print(f"❌ Erro ao contar notificações não lidas: {e}")
            return 0
    
    def cleanup_old_data(self, days_old: int = 30):
        """Remove dados antigos para manter o banco limpo."""
        if not self.client:
            return
            
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Remove notificações antigas
            notifications_result = self.notifications_collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            # Remove histórico antigo
            history_result = self.process_history_collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            print(f"🧹 Limpeza: {notifications_result.deleted_count} notificações e {history_result.deleted_count} registros de histórico removidos")
            
        except Exception as e:
            print(f"❌ Erro na limpeza de dados antigos: {e}")

# Instância global do serviço
notification_service = NotificationService()

