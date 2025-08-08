class FirebaseService:
    """Firebase Service desabilitado - não usado no projeto"""
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Firebase desabilitado - não faz nada"""
        print("🔕 Firebase desabilitado por escolha do usuário.")
        cls._initialized = True
    
    @classmethod
    def send_notification(cls, fcm_token, title, body, data=None):
        """Firebase desabilitado - não envia notificações"""
        print(f"🔕 Notificação ignorada (Firebase desabilitado): {title}")
        return True

