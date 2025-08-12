// Arquivo: src/hooks/useUserMusics.js
// Função: O Gerente de Playlist Pessoal - Mantém a lista de músicas do cliente sempre atualizada.

import { useState, useEffect, useCallback } from 'react';
import { socketService } from '../services/socketService';

const useUserMusics = (userId, token) => {
    const [musics, setMusics] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchMusics = useCallback(async () => {
        if (!userId || !token) {
            setMusics([]);
            setLoading(false);
            return;
        }
        setLoading(true);
        setError(null);
        try {
            // Usando a rota correta da API que definimos no backend
            const response = await fetch(`/api/music/list/user/${userId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });
            if (!response.ok) {
                throw new Error('Falha ao buscar o cardápio de músicas do usuário.');
            }
            const data = await response.json();
            // A rota agora retorna a lista diretamente
            setMusics(data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, [userId, token]);

    useEffect(() => {
        // Busca as músicas na primeira vez que o hook é usado.
        fetchMusics();

        // O Gerente de Playlist fica com o rádio ligado (ouvindo o socketService)
        // para saber quando precisa atualizar o cardápio.
        const handleMusicUpdate = (payload) => {
            // Verifica se o evento é para o usuário atual
            if (payload.user_id === userId) {
                console.log(`📢 Gerente de Playlist ouviu um anúncio sobre as músicas do usuário ${userId}. Atualizando o cardápio...`);
                fetchMusics(); // Revalida os dados buscando a lista mais recente.
            }
        };

        // Ouve os eventos relevantes publicados pelo SyncService do backend
        socketService.on('music_completed', handleMusicUpdate);
        socketService.on('music_deleted', handleMusicUpdate);
        socketService.on('music_requested', handleMusicUpdate);
        socketService.on('music_failed', handleMusicUpdate);

        // Desliga o rádio quando o componente que usa o hook é desmontado
        return () => {
            socketService.off('music_completed', handleMusicUpdate);
            socketService.off('music_deleted', handleMusicUpdate);
            socketService.off('music_requested', handleMusicUpdate);
            socketService.off('music_failed', handleMusicUpdate);
        };
    }, [fetchMusics, userId]);

    return { musics, loading, error, refetch: fetchMusics };
};

export default useUserMusics;
