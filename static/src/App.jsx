// Arquivo: src/App.jsx (VERSÃO HÍBRIDA - Etapa 9)
// Função: O Recepcionista do Restaurante - Valida os clientes e gerencia o acesso.

import { useState, useEffect, createContext } from 'react';
import MusicGenerator from './components/MusicGenerator';
import LoginForm from './components/LoginForm';
import { socketService } from '@/services/socketService.js'; // O rádio do restaurante
import './App.css';

// Criamos o "Crachá Global" (Context) que todos os componentes poderão ler.
export const AuthContext = createContext(null);

function App() {
  // O estado do usuário e do token agora vivem aqui, no ponto mais alto da aplicação.
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('alquimista_token'));
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Função para validar o token quando o app carrega ou o token muda.
    const validateToken = async () => {
      if (token) {
        try {
          // O Recepcionista liga para o backend para verificar a identidade.
          const response = await fetch('/api/profile', {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          
          if (response.ok) {
            const userData = await response.json();
            // Se a identidade for válida, o usuário é confirmado.
            setUser(userData.user);
            // E o rádio principal do restaurante é ligado e configurado para este cliente.
            socketService.connect(token);
          } else {
            // Se o token for inválido, o cliente é barrado.
            setUser(null);
            localStorage.removeItem('alquimista_token');
            socketService.disconnect();
          }
        } catch (error) {
          console.error("Erro de comunicação com a recepção do backend:", error);
          setUser(null);
          localStorage.removeItem('alquimista_token');
          socketService.disconnect();
        }
      }
      setIsLoading(false);
    };

    validateToken();

    // Quando o App for "fechado", o rádio é desligado.
    return () => {
      socketService.disconnect();
    };
  }, [token]);

  // Função que o LoginForm usará quando um cliente fizer login com sucesso.
  const handleLogin = (userData, newToken) => {
    localStorage.setItem('alquimista_token', newToken);
    // Atualiza o token, o que vai disparar o useEffect para validar e conectar o socket.
    setToken(newToken); 
    setUser(userData);
  };

  // Função que o MusicGenerator usará para o logout.
  const handleLogout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('alquimista_token');
    socketService.disconnect(); // Desliga o rádio ao sair.
  };

  // Enquanto o recepcionista valida a identidade, mostramos uma tela de carregamento.
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-xl">Verificando credenciais...</div>
      </div>
    );
  }

  return (
    // O "Crachá Global" é disponibilizado para todos os componentes filhos.
    <AuthContext.Provider value={{ user, token, handleLogin, handleLogout }}>
      <div className="App">
        {user ? (
          // Se o cliente tem um crachá válido, ele entra no estúdio.
          <MusicGenerator />
        ) : (
          // Se não, ele é direcionado para a recepção para fazer o login.
          <LoginForm />
        )}
      </div>
    </AuthContext.Provider>
  );
}

export default App;
