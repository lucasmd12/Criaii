from datetime import datetime
from typing import Dict, Any, List, Optional
from models.notification_models import Notification, ProcessHistory
import asyncio

class NotificationService:
    """Serviço para gerenciar notificações e histórico de processos."""
    
    def __init__(self):
        self.active_processes: Dict[str, Dict[str, Any]] = {}
    
    async def create_notification(self, user_id: str, title: str, message: str, 
                                notification_type: str = "info", metadata: Dict = None) -> str:
        """Cria uma nova notificação para o usuário."""
        try:
            notification_data = {
                'user_id': user_id,
                'title': title,
                'message': message,
                'type': notification_type,
                'read': False,
                'created_at': datetime.utcnow().timestamp(),
                'metadata': metadata or {}
            }
            
            notification = Notification(**notification_data)
            result = await notification.save()
            
            print(f"📢 Notificação criada para {user_id}: {title}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Erro ao criar notificação: {e}")
            return None
    
    async def save_process_history(self, user_id: str, process_id: str, step: str, 
                                 status: str, message: str = "", metadata: Dict = None) -> str:
        """Salva o histórico de um processo."""
        try:
            history_data = {
                'user_id': user_id,
                'process_id': process_id,
                'step': step,
                'status': status,
                'message': message,
                'timestamp': datetime.utcnow().timestamp(),
                'metadata': metadata or {}
            }
            
            history = ProcessHistory(**history_data)
            result = await history.save()
            
            print(f"📝 Histórico salvo: {process_id} - {step} - {status}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Erro ao salvar histórico: {e}")
            return None
    
    async def get_user_notifications(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Recupera notificações do usuário."""
        try:
            notifications = await Notification.find({'user_id': user_id}).sort([('created_at', -1)]).limit(limit).to_list()
            return [notif.dict() for notif in notifications]
        except Exception as e:
            print(f"❌ Erro ao buscar notificações: {e}")
            return []
    
    async def get_unread_count(self, user_id: str) -> int:
        """Conta notificações não lidas do usuário."""
        try:
            count = await Notification.count_documents({'user_id': user_id, 'read': False})
            return count
        except Exception as e:
            print(f"❌ Erro ao contar notificações não lidas: {e}")
            return 0
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Marca uma notificação como lida."""
        try:
            result = await Notification.update_one(
                {'_id': notification_id, 'user_id': user_id},
                {'$set': {'read': True}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Erro ao marcar notificação como lida: {e}")
            return False
    
    async def get_process_history(self, user_id: str, process_id: str = None) -> List[Dict]:
        """Recupera histórico de processos do usuário."""
        try:
            query = {'user_id': user_id}
            if process_id:
                query['process_id'] = process_id
                
            history = await ProcessHistory.find(query).sort([('timestamp', -1)]).to_list()
            return [hist.dict() for hist in history]
        except Exception as e:
            print(f"❌ Erro ao buscar histórico: {e}")
            return []
    
    def start_process_tracking(self, user_id: str, process_id: str, process_type: str = "music_generation"):
        """Inicia o rastreamento de um processo."""
        self.active_processes[process_id] = {
            'user_id': user_id,
            'process_type': process_type,
            'started_at': datetime.utcnow().timestamp(),
            'current_step': 'started',
            'progress': 0
        }
        print(f"🚀 Processo iniciado: {process_id} para usuário {user_id}")
    
    def update_process_progress(self, process_id: str, step: str, progress: int, message: str = ""):
        """Atualiza o progresso de um processo ativo."""
        if process_id in self.active_processes:
            self.active_processes[process_id].update({
                'current_step': step,
                'progress': progress,
                'last_message': message,
                'updated_at': datetime.utcnow().timestamp()
            })
            print(f"📊 Progresso atualizado: {process_id} - {step} ({progress}%)")
    
    def complete_process(self, process_id: str, success: bool = True, final_message: str = ""):
        """Finaliza um processo."""
        if process_id in self.active_processes:
            self.active_processes[process_id].update({
                'completed': True,
                'success': success,
                'final_message': final_message,
                'completed_at': datetime.utcnow().timestamp()
            })
            print(f"✅ Processo finalizado: {process_id} - Sucesso: {success}")
    
    def get_active_process(self, process_id: str) -> Optional[Dict]:
        """Recupera informações de um processo ativo."""
        return self.active_processes.get(process_id)
    
    def cleanup_old_processes(self, max_age_hours: int = 24):
        """Remove processos antigos da memória."""
        current_time = datetime.utcnow().timestamp()
        max_age_seconds = max_age_hours * 3600
        
        to_remove = []
        for process_id, process_data in self.active_processes.items():
            if current_time - process_data.get('started_at', 0) > max_age_seconds:
                to_remove.append(process_id)
        
        for process_id in to_remove:
            del self.active_processes[process_id]
            print(f"🧹 Processo antigo removido: {process_id}")

# Instância global do serviço de notificações
notification_service = NotificationService()

