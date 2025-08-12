# Arquivo: services/notification_service.py (VERSÃO HÍBRIDA FINAL)
# Função: O Arquivista do Restaurante - Registra notificações e histórico no livro principal.

from datetime import datetime
from typing import Dict, Any, List, Optional
from models.notification_models import Notification, ProcessHistory
# ADICIONADO: Importamos as CLASSES dos serviços com os quais ele vai interagir
from services.sync_service import SyncService
from database.database import DatabaseConnection # Para type hinting

class NotificationService:
    """
    Serviço para gerenciar a PERSISTÊNCIA de notificações e histórico de processos.
    Ele colabora com o SyncService para notificar o frontend sobre novas entradas.
    """
    
    def __init__(self):
        # O Arquivista agora precisa de uma linha direta com o Sistema de Comandas
        self.sync_service: Optional[SyncService] = None
        print("🗄️  Arquivista (NotificationService) pronto para registrar os eventos.")

    def set_sync_service(self, sync_service: SyncService):
        """Permite que o main.py injete a dependência do SyncService no startup."""
        self.sync_service = sync_service
        print("✔️  Arquivista recebeu acesso ao Sistema de Comandas para anunciar novos registros.")

    async def create_notification(self, db_manager: DatabaseConnection, user_id: str, title: str, message: str, 
                                notification_type: str = "info", metadata: Dict = None) -> Optional[str]:
        """Cria uma nova notificação, a salva no DB e anuncia no sistema."""
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
            
            # Usando seus modelos Pydantic para salvar no DB
            notification = Notification(**notification_data)
            # Assumindo que seu modelo .save() agora recebe o db_manager
            result = await notification.save(db_manager.db) 
            
            print(f"📢 Notificação registrada no livro para {user_id}: {title}")

            # NOVA RESPONSABILIDADE: Anunciar a nova notificação no sistema de comandas
            if self.sync_service:
                await self.sync_service.publish_event(
                    event_type="new_notification",
                    user_id=user_id,
                    payload=notification.dict() # Envia a notificação inteira para o frontend
                )
                print(f"📡 Arquivista anunciou no sistema: 'Novo aviso no painel do cliente {user_id}!'")

            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Erro ao criar e anunciar notificação: {e}")
            return None
    
    async def save_process_history(self, db_manager: DatabaseConnection, user_id: str, process_id: str, step: str, 
                                 status: str, message: str = "", metadata: Dict = None) -> Optional[str]:
        """Salva uma etapa do histórico de um processo no DB."""
        # Esta função permanece, pois é responsável pela persistência do histórico,
        # que é diferente do estado em tempo real.
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
            result = await history.save(db_manager.db)
            
            # Este log é apenas para o backend, não precisa de evento em tempo real
            # print(f"📝 Histórico salvo: {process_id} - {step} - {status}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Erro ao salvar histórico do processo: {e}")
            return None

    # =================================================================
    # MÉTODOS DE LEITURA (Permanecem os mesmos, mas agora recebem db_manager)
    # =================================================================
    
    async def get_user_notifications(self, db_manager: DatabaseConnection, user_id: str, limit: int = 50, skip: int = 0) -> List[Dict]:
        """Recupera notificações do usuário do DB."""
        try:
            notifications = await Notification.find(
                db_manager.db, {'user_id': user_id}
            ).sort([('created_at', -1)]).skip(skip).limit(limit).to_list()
            return [notif.dict() for notif in notifications]
        except Exception as e:
            print(f"❌ Erro ao buscar notificações do DB: {e}")
            return []
    
    async def get_unread_count(self, db_manager: DatabaseConnection, user_id: str) -> int:
        """Conta notificações não lidas do usuário no DB."""
        try:
            count = await Notification.count_documents(db_manager.db, {'user_id': user_id, 'read': False})
            return count
        except Exception as e:
            print(f"❌ Erro ao contar notificações não lidas do DB: {e}")
            return 0
    
    async def mark_notifications_as_read(self, db_manager: DatabaseConnection, user_id: str, notification_ids: List[str] = None):
        """Marca uma ou mais notificações como lidas no DB."""
        try:
            query = {'user_id': user_id, 'read': False}
            if notification_ids:
                query['_id'] = {'$in': notification_ids}
            
            await Notification.collection(db_manager.db).update_many(
                query,
                {'$set': {'read': True}}
            )
            return True
        except Exception as e:
            print(f"❌ Erro ao marcar notificações como lidas no DB: {e}")
            return False

    async def get_process_history(self, db_manager: DatabaseConnection, user_id: str, limit: int = 20, skip: int = 0) -> List[Dict]:
        """Recupera histórico de processos do usuário do DB."""
        try:
            query = {'user_id': user_id}
            history = await ProcessHistory.find(db_manager.db, query).sort([('timestamp', -1)]).skip(skip).limit(limit).to_list()
            return [hist.dict() for hist in history]
        except Exception as e:
            print(f"❌ Erro ao buscar histórico do DB: {e}")
            return []

    async def get_dashboard_data(self, db_manager: DatabaseConnection, user_id: str) -> Dict:
        # Esta função permanece, pois busca dados agregados do DB.
        # A implementação específica dependeria dos seus modelos.
        print("INFO: get_dashboard_data chamado.")
        return {"message": "Dashboard data not implemented yet."}


# Instância global do serviço de notificações
notification_service = NotificationService()
