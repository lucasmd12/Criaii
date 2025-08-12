// Arquivo: src/services/socketService.js
// Função: O Operador de Rádio do Frontend - Gerencia a conexão com o restaurante.

import { io } from 'socket.io-client';

// A URL do WebSocket agora vem das variáveis de ambiente do Vite.
const SOCKET_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

class SocketService {
    constructor() {
        this.socket = null;
        this.listeners = {}; // Para gerenciar múltiplos ouvintes para o mesmo evento
    }

    connect(token) {
        if (this.socket && this.socket.connected) {
            return;
        }
        
        console.log(`📡 Operador de Rádio tentando conectar ao restaurante em ${SOCKET_URL}`);
        
        // A autenticação agora é feita de forma mais segura via 'auth'
        this.socket = io(SOCKET_URL, {
            path: '/socket.io',
            transports: ['websocket', 'polling'],
            auth: { token }
        });

        this.socket.on('connect', () => {
            console.log('✅ Conexão de rádio estabelecida com o restaurante!');
        });

        this.socket.on('disconnect', () => {
            console.log('🔌 Conexão de rádio com o restaurante foi perdida.');
        });

        this.socket.on('connect_error', (err) => {
            console.error(`❌ Falha na conexão de rádio: ${err.message}`);
        });

        // Ouvinte genérico para todos os eventos do SyncService
        this.socket.on("sync_update", (data) => {
            const { event, data: payload } = data;
            console.log(`📦 Mensagem recebida do Sistema de Comandas: Evento '${event}'`);
            if (this.listeners[event]) {
                this.listeners[event].forEach(callback => callback(payload));
            }
        });
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            console.log('📻 Operador de Rádio desligou o equipamento.');
        }
    }

    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }

    emit(event, data) {
        if (this.socket && this.socket.connected) {
            this.socket.emit(event, data);
        }
    }
}

export const socketService = new SocketService();
