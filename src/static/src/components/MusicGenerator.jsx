import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Music,
  Mic,
  Upload,
  Sparkles,
  Play,
  Download,
  AlertCircle,
  CheckCircle,
  Loader2,
  LogOut,
  User,
  History,
  Pause,
  Bell,
  Clock,
  ChefHat,
  Wifi,
  WifiOff
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import io from 'socket.io-client';

const MusicGenerator = ({ user, onLogout }) => {
  // Estados do formulário
  const [formData, setFormData] = useState({
    description: '',
    lyrics: '',
    musicName: '',
    voiceType: 'instrumental',
    genre: '',
    rhythm: '',
    instruments: '',
    studioType: 'studio'
  });
  
  // Estados da aplicação
  const [voiceFile, setVoiceFile] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [alert, setAlert] = useState(null);
  const [userMusics, setUserMusics] = useState([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentPlayingId, setCurrentPlayingId] = useState(null);
  
  // Estados do WebSocket e progresso
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [currentMessage, setCurrentMessage] = useState('');
  const [estimatedTime, setEstimatedTime] = useState(null);
  const [processId, setProcessId] = useState(null);
  
  // Estados das notificações
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  
  // Refs
  const fileInputRef = useRef(null);
  const audioRef = useRef(null);

  // Conecta ao WebSocket quando o componente monta
  useEffect(() => {
    const newSocket = io('/', {
      transports: ['websocket', 'polling']
    });

    newSocket.on('connect', () => {
      console.log('🔌 Conectado ao WebSocket');
      setIsConnected(true);
      setSocket(newSocket);
      
      // Entra na sala do usuário
      newSocket.emit('join_user_room', { userId: user.id });
    });

    newSocket.on('disconnect', () => {
      console.log('🔌 Desconectado do WebSocket');
      setIsConnected(false);
    });

    newSocket.on('joined_room', (data) => {
      console.log('🏠 Entrou na sala:', data);
    });

    // Eventos de progresso da geração de música
    newSocket.on('music_progress', (data) => {
      console.log('📊 Progresso:', data);
      setProgress(data.progress);
      setCurrentStep(data.step);
      setCurrentMessage(data.message);
      setEstimatedTime(data.estimated_time);
      setProcessId(data.process_id);
    });

    newSocket.on('music_completed', (data) => {
      console.log('✅ Música concluída:', data);
      setProgress(100);
      setCurrentStep('completed');
      setCurrentMessage('🎉 Música servida!');
      setIsGenerating(false);
      
      showAlert('success', `Sua música "${data.music_name}" está pronta!`);
      
      // Recarrega a lista de músicas
      setTimeout(() => {
        loadUserMusics();
        resetProgress();
      }, 2000);
    });

    newSocket.on('music_error', (data) => {
      console.log('❌ Erro na geração:', data);
      setIsGenerating(false);
      resetProgress();
      showAlert('error', `Erro: ${data.error}`);
    });

    return () => {
      newSocket.disconnect();
    };
  }, [user.id]);

  // Carrega músicas do usuário
  useEffect(() => {
    loadUserMusics();
    loadNotifications();
  }, [user]);

  const resetProgress = () => {
    setProgress(0);
    setCurrentStep('');
    setCurrentMessage('');
    setEstimatedTime(null);
    setProcessId(null);
  };

  const loadUserMusics = async () => {
    try {
      const token = localStorage.getItem('alquimista_token');
      const response = await fetch('/api/music/musics', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUserMusics(data.musics || []);
      } else {
        console.error("Falha ao carregar músicas do usuário.");
      }
    } catch (error) {
      console.error('Erro ao carregar músicas:', error);
    }
  };

  const loadNotifications = async () => {
    try {
      const token = localStorage.getItem('alquimista_token');
      const response = await fetch('/api/notifications', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications || []);
        setUnreadCount(data.unread_count || 0);
      }
    } catch (error) {
      console.error('Erro ao carregar notificações:', error);
    }
  };

  const markNotificationAsRead = async (notificationId) => {
    try {
      const token = localStorage.getItem('alquimista_token');
      await fetch(`/api/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      // Atualiza localmente
      setNotifications(prev => 
        prev.map(notif => 
          notif._id === notificationId 
            ? { ...notif, read: true }
            : notif
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Erro ao marcar notificação como lida:', error);
    }
  };

  const showAlert = (type, message) => {
    setAlert({ type, message });
    setTimeout(() => setAlert(null), 5000);
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      const allowedTypes = ['audio/mp3', 'audio/wav', 'audio/m4a', 'audio/ogg', 'audio/flac'];
      if (!allowedTypes.includes(file.type)) {
        showAlert('error', 'Formato não suportado. Use MP3, WAV, M4A, OGG ou FLAC.');
        return;
      }
      
      if (file.size > 50 * 1024 * 1024) {
        showAlert('error', 'Arquivo muito grande. Máximo 50MB.');
        return;
      }
      
      setVoiceFile(file);
      showAlert('success', `Arquivo "${file.name}" selecionado com sucesso!`);
    }
  };

  const handleGenerate = async () => {
    if (!formData.description.trim()) {
      showAlert('error', 'Por favor, descreva o estilo da música.');
      return;
    }
    
    if (!formData.musicName.trim()) {
      showAlert('error', 'Por favor, dê um nome para sua música.');
      return;
    }

    setIsGenerating(true);
    resetProgress();
    showAlert('info', '🍳 Enviando pedido para a cozinha...');

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('description', formData.description);
      formDataToSend.append("musicName", formData.musicName);
      formDataToSend.append("voiceType", formData.voiceType);
      formDataToSend.append('lyrics', formData.lyrics);
      formDataToSend.append('genre', formData.genre);
      formDataToSend.append('rhythm', formData.rhythm);
      formDataToSend.append('instruments', formData.instruments);
      formDataToSend.append('studioType', formData.studioType);
      
      if (voiceFile) {
        formDataToSend.append('voiceSample', voiceFile);
      }

      const token = localStorage.getItem('alquimista_token');
      const response = await fetch('/api/music/generate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formDataToSend,
      });

      if (response.ok) {
        const result = await response.json();
        showAlert('success', result.message);
        
        // Limpa o formulário
        setFormData({ 
          description: '', 
          lyrics: '', 
          musicName: '', 
          voiceType: 'instrumental',
          genre: '',
          rhythm: '',
          instruments: '',
          studioType: 'studio'
        });
        setVoiceFile(null);
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao gerar música');
      }
    } catch (error) {
      console.error('Erro:', error);
      showAlert('error', error.message || 'Erro ao gerar música. Tente novamente.');
      setIsGenerating(false);
      resetProgress();
    }
  };

  const handlePlay = (musicUrl, musicId) => {
    if (currentPlayingId === musicId && isPlaying) {
      audioRef.current?.pause();
      setIsPlaying(false);
      setCurrentPlayingId(null);
    } else {
      if (audioRef.current) {
        audioRef.current.src = musicUrl;
        audioRef.current.play();
        setIsPlaying(true);
        setCurrentPlayingId(musicId);
      }
    }
  };

  const handleDownload = (musicUrl, musicName) => {
    const link = document.createElement('a');
    link.href = musicUrl;
    link.download = `${musicName}.mp3`;
    link.click();
    showAlert('success', 'Download iniciado!');
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return "";
    return new Date(timestamp * 1000).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStepIcon = (step) => {
    const icons = {
      'received': '📋',
      'connecting': '🔌',
      'sending_order': '📝',
      'preparing': '👨‍🍳',
      'processing_voice': '🎤',
      'cooking': '🔥',
      'waiting_result': '⏳',
      'finalizing': '🎵',
      'uploading': '☁️',
      'saving': '💾',
      'completed': '🎉'
    };
    return icons[step] || '⚙️';
  };

  const getStepDescription = (step) => {
    const descriptions = {
      'received': 'Pedido recebido',
      'connecting': 'Conectando com a cozinha',
      'sending_order': 'Enviando pedido',
      'preparing': 'Chef IA analisando o pedido',
      'processing_voice': 'Processando sua voz',
      'cooking': 'No forno da IA',
      'waiting_result': 'Aguardando resultado',
      'finalizing': 'Finalizando detalhes',
      'uploading': 'Garçom levando à mesa',
      'saving': 'Registrando no cardápio',
      'completed': 'Música servida!'
    };
    return descriptions[step] || 'Processando...';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full">
              <Music className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-white">Alquimista Musical</h1>
              <p className="text-purple-200">
                Bem-vindo, {user.username}! Transforme suas ideias em música
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Status da conexão */}
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
              isConnected ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'
            }`}>
              {isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
              <span className="text-sm">
                {isConnected ? 'Conectado' : 'Desconectado'}
              </span>
            </div>
            
            <div className="flex items-center gap-2 text-white bg-white/10 px-3 py-2 rounded-lg">
              <User className="w-4 h-4" />
              <span>{user.username}</span>
            </div>
            <Button
              onClick={onLogout}
              variant="outline"
              className="border-white/20 text-white hover:bg-white/10"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Sair
            </Button>
          </div>
        </motion.div>

        {/* Alert */}
        <AnimatePresence>
          {alert && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-6"
            >
              <Alert className={`${
                alert.type === 'error' ? 'border-red-500 bg-red-50' : 
                alert.type === 'success' ? 'border-green-500 bg-green-50' :
                'border-blue-500 bg-blue-50'
              }`}>
                {alert.type === 'error' ? 
                  <AlertCircle className="h-4 w-4 text-red-600" /> : 
                  alert.type === 'success' ?
                  <CheckCircle className="h-4 w-4 text-green-600" /> :
                  <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                }
                <AlertDescription className={
                  alert.type === 'error' ? 'text-red-800' : 
                  alert.type === 'success' ? 'text-green-800' :
                  'text-blue-800'
                }>
                  {alert.message}
                </AlertDescription>
              </Alert>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Tabs principais */}
        <Tabs defaultValue="create" className="w-full">
          <TabsList className="grid w-full grid-cols-4 bg-white/10 backdrop-blur-lg">
            <TabsTrigger value="create" className="text-white data-[state=active]:bg-purple-500">
              <Sparkles className="w-4 h-4 mr-2" />
              Criar Música
            </TabsTrigger>
            <TabsTrigger value="progress" className="text-white data-[state=active]:bg-purple-500">
              <ChefHat className="w-4 h-4 mr-2" />
              Acompanhar Processo
            </TabsTrigger>
            <TabsTrigger value="musics" className="text-white data-[state=active]:bg-purple-500">
              <History className="w-4 h-4 mr-2" />
              Suas Músicas
            </TabsTrigger>
            <TabsTrigger value="notifications" className="text-white data-[state=active]:bg-purple-500 relative">
              <Bell className="w-4 h-4 mr-2" />
              Notificações
              {unreadCount > 0 && (
                <Badge className="absolute -top-2 -right-2 bg-red-500 text-white text-xs">
                  {unreadCount}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          {/* Aba Criar Música */}
          <TabsContent value="create" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Formulário */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                <Card className="bg-white/10 backdrop-blur-lg border-white/20">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-purple-400" />
                      Estúdio Virtual
                    </CardTitle>
                    <CardDescription className="text-purple-200">
                      Descreva sua visão musical e deixe a IA trabalhar a magia
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Nome da Música */}
                    <div className="space-y-2">
                      <Label htmlFor="musicName" className="text-white">
                        Nome da Música *
                      </Label>
                      <Input
                        id="musicName"
                        placeholder="Ex: Noite Chuvosa no Rio"
                        value={formData.musicName}
                        onChange={(e) => setFormData(prev => ({ ...prev, musicName: e.target.value }))}
                        className="bg-white/10 border-white/20 text-white placeholder:text-purple-300"
                      />
                    </div>

                    {/* Descrição */}
                    <div className="space-y-2">
                      <Label htmlFor="description" className="text-white">
                        Descrição/Prompt da Música *
                      </Label>
                      <Textarea
                        id="description"
                        placeholder="Ex: Uma bossa nova melancólica com piano suave, como uma noite chuvosa no Rio de Janeiro..."
                        value={formData.description}
                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                        className="bg-white/10 border-white/20 text-white placeholder:text-purple-300"
                        rows={3}
                      />
                    </div>

                    {/* Tipo de Voz */}
                    <div className="space-y-2">
                      <Label className="text-white">Tipo de Voz *</Label>
                      <div className="grid grid-cols-2 gap-2">
                        {[
                          { value: 'instrumental', label: 'Instrumental' },
                          { value: 'male', label: 'Voz Masculina' },
                          { value: 'female', label: 'Voz Feminina' },
                          { value: 'both', label: 'Dueto' }
                        ].map((option) => (
                          <Button
                            key={option.value}
                            type="button"
                            variant={formData.voiceType === option.value ? "default" : "outline"}
                            onClick={() => setFormData(prev => ({ ...prev, voiceType: option.value }))}
                            className={`${
                              formData.voiceType === option.value 
                                ? 'bg-purple-500 text-white' 
                                : 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                            }`}
                          >
                            {option.label}
                          </Button>
                        ))}
                      </div>
                    </div>

                    {/* Campos opcionais */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Gênero */}
                      <div className="space-y-2">
                        <Label htmlFor="genre" className="text-white">
                          Gênero Musical
                        </Label>
                        <Input
                          id="genre"
                          placeholder="Ex: Rock, Pop, Sertanejo..."
                          value={formData.genre}
                          onChange={(e) => setFormData(prev => ({ ...prev, genre: e.target.value }))}
                          className="bg-white/10 border-white/20 text-white placeholder:text-purple-300"
                        />
                      </div>

                      {/* Ritmo */}
                      <div className="space-y-2">
                        <Label className="text-white">Ritmo</Label>
                        <div className="grid grid-cols-3 gap-1">
                          {[
                            { value: 'slow', label: 'Lento' },
                            { value: 'fast', label: 'Rápido' },
                            { value: 'mixed', label: 'Misto' }
                          ].map((option) => (
                            <Button
                              key={option.value}
                              type="button"
                              size="sm"
                              variant={formData.rhythm === option.value ? "default" : "outline"}
                              onClick={() => setFormData(prev => ({ 
                                ...prev, 
                                rhythm: prev.rhythm === option.value ? '' : option.value 
                              }))}
                              className={`${
                                formData.rhythm === option.value 
                                  ? 'bg-purple-500 text-white' 
                                  : 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                              }`}
                            >
                              {option.label}
                            </Button>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Instrumentos */}
                    <div className="space-y-2">
                      <Label htmlFor="instruments" className="text-white">
                        Instrumentos Específicos
                      </Label>
                      <Input
                        id="instruments"
                        placeholder="Ex: Piano, Violão, Bateria..."
                        value={formData.instruments}
                        onChange={(e) => setFormData(prev => ({ ...prev, instruments: e.target.value }))}
                        className="bg-white/10 border-white/20 text-white placeholder:text-purple-300"
                      />
                    </div>

                    {/* Ambiente de Gravação */}
                    <div className="space-y-2">
                      <Label className="text-white">Ambiente de Gravação</Label>
                      <div className="grid grid-cols-2 gap-2">
                        {[
                          { value: 'studio', label: 'Estúdio' },
                          { value: 'live', label: 'Ao Vivo' }
                        ].map((option) => (
                          <Button
                            key={option.value}
                            type="button"
                            variant={formData.studioType === option.value ? "default" : "outline"}
                            onClick={() => setFormData(prev => ({ ...prev, studioType: option.value }))}
                            className={`${
                              formData.studioType === option.value 
                                ? 'bg-purple-500 text-white' 
                                : 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                            }`}
                          >
                            {option.label}
                          </Button>
                        ))}
                      </div>
                    </div>

                    {/* Letra */}
                    <div className="space-y-2">
                      <Label htmlFor="lyrics" className="text-white">
                        Letra da Música (Opcional)
                      </Label>
                      <Textarea
                        id="lyrics"
                        placeholder="Digite aqui a letra da sua música..."
                        value={formData.lyrics}
                        onChange={(e) => setFormData(prev => ({ ...prev, lyrics: e.target.value }))}
                        className="bg-white/10 border-white/20 text-white placeholder:text-purple-300"
                        rows={4}
                      />
                    </div>

                    {/* Canta aí, solte a voz */}
                    {formData.voiceType !== 'instrumental' && (
                      <div className="space-y-2">
                        <Label className="text-white">🎤 Canta aí, solte a voz! (Opcional)</Label>
                        <div className="flex flex-col gap-3">
                          <Button
                            type="button"
                            variant="outline"
                            onClick={() => fileInputRef.current?.click()}
                            className="bg-white/10 border-white/20 text-white hover:bg-white/20 justify-start"
                          >
                            {voiceFile ? (
                              <>
                                <CheckCircle className="w-4 h-4 mr-2 text-green-400" />
                                {voiceFile.name}
                              </>
                            ) : (
                              <>
                                <Upload className="w-4 h-4 mr-2" />
                                Gravar ou enviar sua voz (até 5 min)
                              </>
                            )}
                          </Button>
                          <input
                            ref={fileInputRef}
                            type="file"
                            accept="audio/*"
                            onChange={handleFileSelect}
                            className="hidden"
                          />
                          <div className="flex flex-wrap gap-2">
                            <Badge variant="secondary" className="bg-white/10 text-purple-200">MP3</Badge>
                            <Badge variant="secondary" className="bg-white/10 text-purple-200">WAV</Badge>
                            <Badge variant="secondary" className="bg-white/10 text-purple-200">M4A</Badge>
                            <Badge variant="secondary" className="bg-white/10 text-purple-200">Max 50MB</Badge>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Botão Gerar */}
                    <Button
                      onClick={handleGenerate}
                      disabled={isGenerating || !isConnected}
                      className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold py-3 text-lg"
                    >
                      {isGenerating ? (
                        <>
                          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                          Criando Magia Musical...
                        </>
                      ) : !isConnected ? (
                        <>
                          <WifiOff className="w-5 h-5 mr-2" />
                          Conectando...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-5 h-5 mr-2" />
                          Gerar Minha Música
                        </>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Preview/Instruções */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 }}
              >
                <Card className="bg-white/10 backdrop-blur-lg border-white/20">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <ChefHat className="w-5 h-5 text-purple-400" />
                      Como Funciona o Estúdio
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-3 text-purple-200">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">🍽️</span>
                        <div>
                          <h4 className="font-semibold text-white">Restaurante Musical</h4>
                          <p className="text-sm">Você é o cliente com um cardápio inteligente de opções musicais</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">👨‍🍳</span>
                        <div>
                          <h4 className="font-semibold text-white">Cozinha IA</h4>
                          <p className="text-sm">Nossa IA trabalha como chef, criando sua música com precisão</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">👀</span>
                        <div>
                          <h4 className="font-semibold text-white">Vidro da Cozinha</h4>
                          <p className="text-sm">Acompanhe cada etapa do processo em tempo real</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">🎵</span>
                        <div>
                          <h4 className="font-semibold text-white">Música Servida</h4>
                          <p className="text-sm">Receba sua criação musical pronta para download</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          </TabsContent>

          {/* Aba Acompanhar Processo */}
          <TabsContent value="progress" className="mt-6">
            <Card className="bg-white/10 backdrop-blur-lg border-white/20">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <ChefHat className="w-5 h-5 text-purple-400" />
                  Vidro da Cozinha - Acompanhe em Tempo Real
                </CardTitle>
                <CardDescription className="text-purple-200">
                  Veja cada etapa do processo de criação da sua música
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isGenerating ? (
                  <div className="space-y-6">
                    {/* Barra de Progresso Principal */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-white">
                        <span className="font-semibold">Progresso Geral</span>
                        <span className="text-lg font-bold">{Math.round(progress)}%</span>
                      </div>
                      <Progress value={progress} className="h-3 bg-white/20" />
                    </div>

                    {/* Etapa Atual */}
                    {currentStep && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center gap-4 p-4 bg-white/10 rounded-lg"
                      >
                        <span className="text-3xl">{getStepIcon(currentStep)}</span>
                        <div className="flex-1">
                          <h3 className="text-white font-semibold">
                            {getStepDescription(currentStep)}
                          </h3>
                          {currentMessage && (
                            <p className="text-purple-200 text-sm">{currentMessage}</p>
                          )}
                          {estimatedTime && (
                            <div className="flex items-center gap-2 mt-2 text-purple-300 text-sm">
                              <Clock className="w-4 h-4" />
                              <span>Tempo estimado: {estimatedTime}s</span>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}

                    {/* ID do Processo */}
                    {processId && (
                      <div className="text-center text-purple-300 text-sm">
                        ID do Processo: {processId}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <ChefHat className="w-16 h-16 text-purple-400 mx-auto mb-4" />
                    <h3 className="text-white text-xl font-semibold mb-2">
                      Cozinha Pronta para Trabalhar
                    </h3>
                    <p className="text-purple-200">
                      Faça seu pedido na aba "Criar Música" para acompanhar o processo aqui
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Aba Suas Músicas */}
          <TabsContent value="musics" className="mt-6">
            <Card className="bg-white/10 backdrop-blur-lg border-white/20">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <History className="w-5 h-5 text-purple-400" />
                  Suas Músicas
                </CardTitle>
                <CardDescription className="text-purple-200">
                  {userMusics.length} música{userMusics.length !== 1 ? 's' : ''} criada{userMusics.length !== 1 ? 's' : ''}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {userMusics.length > 0 ? (
                  <div className="space-y-4">
                    {userMusics.map((music) => (
                      <motion.div
                        key={music._id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center justify-between p-4 bg-white/10 rounded-lg"
                      >
                        <div className="flex-1">
                          <h3 className="text-white font-semibold">{music.music_name}</h3>
                          <p className="text-purple-200 text-sm">{music.description}</p>
                          <div className="flex items-center gap-4 mt-2 text-purple-300 text-sm">
                            <span>Tipo: {music.voice_type}</span>
                            {music.genre && <span>Gênero: {music.genre}</span>}
                            <span>{formatDate(music.timestamp)}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handlePlay(music.music_url, music._id)}
                            className="bg-white/10 border-white/20 text-white hover:bg-white/20"
                          >
                            {currentPlayingId === music._id && isPlaying ? (
                              <Pause className="w-4 h-4" />
                            ) : (
                              <Play className="w-4 h-4" />
                            )}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDownload(music.music_url, music.music_name)}
                            className="bg-white/10 border-white/20 text-white hover:bg-white/20"
                          >
                            <Download className="w-4 h-4" />
                          </Button>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Music className="w-16 h-16 text-purple-400 mx-auto mb-4" />
                    <h3 className="text-white text-xl font-semibold mb-2">
                      Nenhuma música criada ainda
                    </h3>
                    <p className="text-purple-200">
                      Crie sua primeira obra-prima musical!
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Aba Notificações */}
          <TabsContent value="notifications" className="mt-6">
            <Card className="bg-white/10 backdrop-blur-lg border-white/20">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Bell className="w-5 h-5 text-purple-400" />
                  Central de Notificações
                  {unreadCount > 0 && (
                    <Badge className="bg-red-500 text-white">
                      {unreadCount} não lidas
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription className="text-purple-200">
                  Histórico de processos e notificações do sistema
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-96">
                  {notifications.length > 0 ? (
                    <div className="space-y-3">
                      {notifications.map((notification) => (
                        <motion.div
                          key={notification._id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          className={`p-4 rounded-lg cursor-pointer transition-all ${
                            notification.read 
                              ? 'bg-white/5 border-white/10' 
                              : 'bg-white/15 border-purple-400/50'
                          } border`}
                          onClick={() => !notification.read && markNotificationAsRead(notification._id)}
                        >
                          <div className="flex items-start gap-3">
                            <span className="text-2xl">
                              {notification.type === 'success' ? '✅' : 
                               notification.type === 'error' ? '❌' : 
                               notification.type === 'info' ? 'ℹ️' : '📢'}
                            </span>
                            <div className="flex-1">
                              <h4 className={`font-semibold ${
                                notification.read ? 'text-purple-200' : 'text-white'
                              }`}>
                                {notification.title}
                              </h4>
                              <p className={`text-sm ${
                                notification.read ? 'text-purple-300' : 'text-purple-100'
                              }`}>
                                {notification.message}
                              </p>
                              <div className="flex items-center gap-2 mt-2 text-xs text-purple-400">
                                <Clock className="w-3 h-3" />
                                <span>{formatDate(notification.created_at)}</span>
                                {!notification.read && (
                                  <Badge className="bg-purple-500 text-white text-xs">
                                    Nova
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <Bell className="w-16 h-16 text-purple-400 mx-auto mb-4" />
                      <h3 className="text-white text-xl font-semibold mb-2">
                        Nenhuma notificação
                      </h3>
                      <p className="text-purple-200">
                        Suas notificações aparecerão aqui
                      </p>
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Audio player oculto */}
        <audio
          ref={audioRef}
          onEnded={() => {
            setIsPlaying(false);
            setCurrentPlayingId(null);
          }}
          onError={() => {
            setIsPlaying(false);
            setCurrentPlayingId(null);
            showAlert('error', 'Erro ao reproduzir música');
          }}
        />
      </div>
    </div>
  );
};

export default MusicGenerator;

