import React, { useState, useEffect } from 'react';
import { Trash2, Plus, Calculator, ChevronDown, ChevronUp, Loader2, Wrench, DollarSign, TrendingUp, Package, Sparkles, BarChart3 } from 'lucide-react';

// ===== COMPONENTES UI =====
const Card = ({ children, className = '' }) => (
  <div className={`bg-white rounded-lg shadow ${className}`}>{children}</div>
);

const CardHeader = ({ children, className = '' }) => (
  <div className={`p-6 ${className}`}>{children}</div>
);

const CardTitle = ({ children, className = '' }) => (
  <h3 className={`text-2xl font-semibold ${className}`}>{children}</h3>
);

const CardContent = ({ children, className = '' }) => (
  <div className={`p-6 pt-0 ${className}`}>{children}</div>
);

const Button = ({ children, onClick, className = '', variant = 'default', size = 'default', ...props }) => {
  const baseStyles = 'inline-flex items-center justify-center rounded-lg font-medium transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none';
  
  const variants = {
    default: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    ghost: 'hover:bg-gray-100 text-gray-700',
    outline: 'border border-gray-300 bg-white hover:bg-gray-50'
  };
  
  const sizes = {
    default: 'px-4 py-2 text-sm',
    sm: 'px-3 py-1.5 text-xs',
    icon: 'h-10 w-10 p-0'
  };
  
  return (
    <button
      onClick={onClick}
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

const Input = ({ className = '', ...props }) => (
  <input
    className={`flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 ${className}`}
    {...props}
  />
);

// ===== API CLIENT MOCK =====
const apiClient = {
  get: async () => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return { data: [] };
  },
  post: async (endpoint, data) => {
    await new Promise(resolve => setTimeout(resolve, 300));
    return { data: { ...data, id: Date.now() } };
  },
  put: async () => {
    await new Promise(resolve => setTimeout(resolve, 300));
    return { data: {} };
  },
  delete: async () => {
    await new Promise(resolve => setTimeout(resolve, 300));
    return { success: true };
  }
};

// ===== COMPONENTE PRINCIPAL =====
export default function FinancialControl() {
  const [machines, setMachines] = useState([]);
  const [expandedMachine, setExpandedMachine] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadMachines();
  }, []);

  const loadMachines = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/machines');
      const data = Array.isArray(response?.data) ? response.data : [];
      setMachines(data);
    } catch (error) {
      console.error('Erro ao carregar máquinas:', error);
      setError(error.message || 'Erro ao carregar máquinas');
      setMachines([]);
    } finally {
      setLoading(false);
    }
  };

  const saveMachine = async (machine) => {
    try {
      setSaving(true);
      if (machine.id) {
        await apiClient.put(`/machines/${machine.id}`, machine);
      } else {
        const response = await apiClient.post('/machines', machine);
        setMachines(prev => prev.map(m => 
          m.tempId === machine.tempId ? response.data : m
        ));
      }
    } catch (error) {
      console.error('Erro ao salvar máquina:', error);
    } finally {
      setSaving(false);
    }
  };

  const debouncedSave = (machine) => {
    clearTimeout(window.machineTimeout);
    window.machineTimeout = setTimeout(() => saveMachine(machine), 1000);
  };

  const addMachine = () => {
    const tempId = Date.now();
    const newMachine = {
      tempId,
      name: '',
      services: [],
      expenses: [],
      labor: 0
    };
    setMachines([...machines, newMachine]);
    setExpandedMachine(tempId);
  };

  const removeMachine = async (machine) => {
    if (!confirm('Deseja realmente excluir esta máquina?')) return;
    
    try {
      if (machine.id) {
        await apiClient.delete(`/machines/${machine.id}`);
      }
      setMachines(machines.filter(m => 
        (m.id || m.tempId) !== (machine.id || machine.tempId)
      ));
      if (expandedMachine === (machine.id || machine.tempId)) {
        setExpandedMachine(null);
      }
    } catch (error) {
      console.error('Erro ao deletar máquina:', error);
    }
  };

  const updateMachine = (machineId, updates) => {
    const updatedMachines = machines.map(m => {
      const id = m.id || m.tempId;
      if (id === machineId) {
        const updated = { ...m, ...updates };
        debouncedSave(updated);
        return updated;
      }
      return m;
    });
    setMachines(updatedMachines);
  };

  const addService = (machineId) => {
    const machine = machines.find(m => (m.id || m.tempId) === machineId);
    updateMachine(machineId, {
      services: [...machine.services, { name: '', value: 0 }]
    });
  };

  const updateService = (machineId, serviceIndex, field, value) => {
    const machine = machines.find(m => (m.id || m.tempId) === machineId);
    const newServices = [...machine.services];
    newServices[serviceIndex] = {
      ...newServices[serviceIndex],
      [field]: field === 'value' ? (parseFloat(value) || 0) : value
    };
    updateMachine(machineId, { services: newServices });
  };

  const removeService = (machineId, serviceIndex) => {
    const machine = machines.find(m => (m.id || m.tempId) === machineId);
    updateMachine(machineId, {
      services: machine.services.filter((_, i) => i !== serviceIndex)
    });
  };

  const addExpense = (machineId) => {
    const machine = machines.find(m => (m.id || m.tempId) === machineId);
    updateMachine(machineId, {
      expenses: [...machine.expenses, { name: '', value: 0 }]
    });
  };

  const updateExpense = (machineId, expenseIndex, field, value) => {
    const machine = machines.find(m => (m.id || m.tempId) === machineId);
    const newExpenses = [...machine.expenses];
    newExpenses[expenseIndex] = {
      ...newExpenses[expenseIndex],
      [field]: field === 'value' ? (parseFloat(value) || 0) : value
    };
    updateMachine(machineId, { expenses: newExpenses });
  };

  const removeExpense = (machineId, expenseIndex) => {
    const machine = machines.find(m => (m.id || m.tempId) === machineId);
    updateMachine(machineId, {
      expenses: machine.expenses.filter((_, i) => i !== expenseIndex)
    });
  };

  const calculateMachineTotal = (machine) => {
    const totalServices = machine.services.reduce((sum, s) => sum + (s.value || 0), 0);
    const totalExpenses = machine.expenses.reduce((sum, e) => sum + (e.value || 0), 0);
    return totalServices + (machine.labor || 0) - totalExpenses;
  };

  const calculateGlobalTotals = () => {
    let totalRevenue = 0;
    let totalExpenses = 0;
    
    if (Array.isArray(machines)) {
      machines.forEach(machine => {
        totalRevenue += machine.services.reduce((sum, s) => sum + (s.value || 0), 0) + (machine.labor || 0);
        totalExpenses += machine.expenses.reduce((sum, e) => sum + (e.value || 0), 0);
      });
    }
    
    const profit = totalRevenue - totalExpenses;
    const motherShare = profit * 0.7;
    const yourShare = profit * 0.3;
    
    return { totalRevenue, totalExpenses, profit, motherShare, yourShare };
  };

  const totals = calculateGlobalTotals();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900">
        <div className="text-center">
          <Loader2 className="animate-spin h-16 w-16 text-blue-400 mx-auto mb-4" />
          <p className="text-white text-xl font-semibold">Carregando sistema...</p>
          <p className="text-blue-300 text-sm mt-2">Aguarde um momento</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-950 via-red-950 to-slate-900">
        <div className="text-center bg-white/10 backdrop-blur-lg p-8 rounded-2xl border border-red-500/20">
          <div className="bg-red-500/20 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">⚠️</span>
          </div>
          <p className="text-red-400 text-xl mb-4 font-semibold">❌ {error}</p>
          <Button onClick={loadMachines} className="bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800">
            Tentar Novamente
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 rounded-3xl shadow-2xl overflow-hidden">
          <div className="bg-black/20 backdrop-blur-sm">
            <CardHeader className="pb-4">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="bg-white/20 p-4 rounded-2xl backdrop-blur-sm border border-white/30 shadow-xl">
                    <Calculator className="text-white" size={40} />
                  </div>
                  <div>
                    <CardTitle className="text-3xl md:text-4xl font-black text-white mb-1 tracking-tight">
                      Controle Financeiro Pro
                    </CardTitle>
                    <p className="text-white/90 font-medium flex items-center gap-2">
                      <Sparkles size={16} className="animate-pulse" />
                      Sistema de Gestão de Máquinas • Uberlândia, MG
                    </p>
                  </div>
                </div>
                <Button 
                  onClick={addMachine} 
                  className="bg-white text-blue-600 hover:bg-blue-50 font-bold shadow-xl hover:shadow-2xl transition-all hover:scale-105"
                >
                  <Plus size={20} className="mr-2" />
                  Nova Máquina
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 md:gap-4">
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 border border-white/20 hover:bg-white/20 transition-all hover:scale-105 cursor-pointer group">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-white/80 text-xs font-bold uppercase tracking-wider">Receita</p>
                    <TrendingUp size={16} className="text-emerald-300 group-hover:scale-110 transition-transform" />
                  </div>
                  <p className="text-2xl md:text-3xl font-black text-white">
                    R$ {totals.totalRevenue.toFixed(2)}
                  </p>
                  <div className="h-1 bg-gradient-to-r from-emerald-400 to-green-500 rounded-full mt-2"></div>
                </div>
                
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 border border-white/20 hover:bg-white/20 transition-all hover:scale-105 cursor-pointer group">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-white/80 text-xs font-bold uppercase tracking-wider">Despesas</p>
                    <Package size={16} className="text-red-300 group-hover:scale-110 transition-transform" />
                  </div>
                  <p className="text-2xl md:text-3xl font-black text-white">
                    R$ {totals.totalExpenses.toFixed(2)}
                  </p>
                  <div className="h-1 bg-gradient-to-r from-red-400 to-pink-500 rounded-full mt-2"></div>
                </div>
                
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 border border-white/20 hover:bg-white/20 transition-all hover:scale-105 cursor-pointer group">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-white/80 text-xs font-bold uppercase tracking-wider">Lucro</p>
                    <BarChart3 size={16} className="text-yellow-300 group-hover:scale-110 transition-transform" />
                  </div>
                  <p className="text-2xl md:text-3xl font-black text-emerald-300">
                    R$ {totals.profit.toFixed(2)}
                  </p>
                  <div className="h-1 bg-gradient-to-r from-yellow-400 to-emerald-500 rounded-full mt-2"></div>
                </div>
                
                <div className="bg-gradient-to-br from-yellow-500/20 to-orange-500/20 backdrop-blur-lg rounded-2xl p-4 border border-yellow-400/30 hover:from-yellow-500/30 hover:to-orange-500/30 transition-all hover:scale-105 cursor-pointer group">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-yellow-200 text-xs font-bold uppercase tracking-wider">Mãe (70%)</p>
                    <DollarSign size={16} className="text-yellow-300 group-hover:scale-110 transition-transform" />
                  </div>
                  <p className="text-2xl md:text-3xl font-black text-yellow-100">
                    R$ {totals.motherShare.toFixed(2)}
                  </p>
                  <div className="h-1 bg-gradient-to-r from-yellow-300 to-orange-400 rounded-full mt-2"></div>
                </div>
                
                <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 backdrop-blur-lg rounded-2xl p-4 border border-green-400/30 hover:from-green-500/30 hover:to-emerald-500/30 transition-all hover:scale-105 cursor-pointer group">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-green-200 text-xs font-bold uppercase tracking-wider">Você (30%)</p>
                    <Sparkles size={16} className="text-green-300 group-hover:scale-110 transition-transform animate-pulse" />
                  </div>
                  <p className="text-2xl md:text-3xl font-black text-green-100">
                    R$ {totals.yourShare.toFixed(2)}
                  </p>
                  <div className="h-1 bg-gradient-to-r from-green-300 to-emerald-400 rounded-full mt-2"></div>
                </div>
              </div>
            </CardContent>
          </div>
        </div>

        <div className="space-y-4">
          {machines.map((machine) => {
            const machineId = machine.id || machine.tempId;
            const isExpanded = expandedMachine === machineId;
            const machineTotal = calculateMachineTotal(machine);
            const totalServices = machine.services.reduce((sum, s) => sum + (s.value || 0), 0);
            const totalExpensesM = machine.expenses.reduce((sum, e) => sum + (e.value || 0), 0);
            
            return (
              <Card key={machineId} className="overflow-hidden bg-white/95 backdrop-blur-sm border-2 border-gray-200 hover:border-blue-400 transition-all hover:shadow-2xl">
                <div 
                  className="flex items-center justify-between p-5 cursor-pointer hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 transition-all"
                  onClick={() => setExpandedMachine(isExpanded ? null : machineId)}
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className={`p-3 rounded-xl shadow-lg transition-all ${
                      machineTotal >= 0 
                        ? 'bg-gradient-to-br from-green-400 to-emerald-500' 
                        : 'bg-gradient-to-br from-red-400 to-pink-500'
                    }`}>
                      <Wrench className="text-white" size={28} />
                    </div>
                    <div className="flex-1">
                      <Input
                        type="text"
                        value={machine.name}
                        onChange={(e) => {
                          e.stopPropagation();
                          updateMachine(machineId, { name: e.target.value });
                        }}
                        onClick={(e) => e.stopPropagation()}
                        placeholder="Nome da máquina... (ex: Lavadora Samsung 12kg)"
                        className="text-xl font-bold border-none bg-transparent focus:ring-0 p-0 placeholder:text-gray-400"
                      />
                      <div className="flex items-center gap-4 mt-2">
                        <p className="text-sm text-gray-600 font-medium flex items-center gap-1">
                          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                          {machine.services.length} serviços
                        </p>
                        <p className="text-sm text-gray-600 font-medium flex items-center gap-1">
                          <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                          {machine.expenses.length} despesas
                        </p>
                        <p className="text-sm text-gray-600 font-medium flex items-center gap-1">
                          <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                          R$ {(machine.labor || 0).toFixed(2)} mão de obra
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right bg-gradient-to-br from-gray-50 to-gray-100 p-4 rounded-xl border-2 border-gray-200">
                      <p className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Total Líquido</p>
                      <p className={`text-3xl font-black ${
                        machineTotal >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        R$ {machineTotal.toFixed(2)}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeMachine(machine);
                      }}
                      className="text-red-500 hover:text-red-700 hover:bg-red-50 transition-all"
                    >
                      <Trash2 size={22} />
                    </Button>
                    <div className={`p-2 rounded-lg transition-all ${isExpanded ? 'bg-blue-100 rotate-180' : 'bg-gray-100'}`}>
                      <ChevronDown size={24} className="text-gray-700" />
                    </div>
                  </div>
                </div>

                {isExpanded && (
                  <CardContent className="border-t-2 bg-gradient-to-br from-gray-50 to-blue-50/30 p-6">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-5 border-2 border-green-300 shadow-lg">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-2">
                            <div className="bg-green-500 p-2 rounded-lg">
                              <TrendingUp className="text-white" size={18} />
                            </div>
                            <h3 className="font-black text-green-800 text-base uppercase tracking-wide">Serviços</h3>
                          </div>
                          <Button
                            size="sm"
                            onClick={() => addService(machineId)}
                            className="bg-green-600 hover:bg-green-700 text-white h-9 px-3 shadow-md hover:shadow-lg transition-all"
                          >
                            <Plus size={16} className="mr-1" />
                            Adicionar
                          </Button>
                        </div>
                        <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
                          {machine.services.map((service, idx) => (
                            <div key={idx} className="flex gap-2 bg-white p-3 rounded-xl border border-green-200 hover:border-green-400 transition-all">
                              <Input
                                placeholder="Nome do serviço"
                                value={service.name}
                                onChange={(e) => updateService(machineId, idx, 'name', e.target.value)}
                                className="text-sm font-medium border-green-200 focus:border-green-400"
                              />
                              <div className="relative">
                                <span className="absolute left-3 top-2.5 text-green-600 font-bold">R$</span>
                                <Input
                                  type="number"
                                  step="0.01"
                                  placeholder="0.00"
                                  value={service.value || ''}
                                  onChange={(e) => updateService(machineId, idx, 'value', e.target.value)}
                                  className="w-28 text-sm font-bold pl-9 border-green-200 focus:border-green-400"
                                />
                              </div>
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => removeService(machineId, idx)}
                                className="text-red-500 hover:text-red-700 hover:bg-red-50 h-10 w-10"
                              >
                                <Trash2 size={18} />
                              </Button>
                            </div>
                          ))}
                          {machine.services.length === 0 && (
                            <div className="text-center py-8">
                              <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                                <TrendingUp className="text-green-600" size={28} />
                              </div>
                              <p className="text-gray-500 text-sm font-medium">Nenhum serviço cadastrado</p>
                            </div>
                          )}
                        </div>
                        <div className="mt-4 pt-4 border-t-2 border-green-300 bg-green-100 -mx-5 -mb-5 px-5 py-3 rounded-b-2xl">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-bold text-green-800 uppercase">Subtotal Serviços:</span>
                            <span className="text-xl font-black text-green-700">R$ {totalServices.toFixed(2)}</span>
                          </div>
                        </div>
                      </div>

                      <div className="bg-gradient-to-br from-red-50 to-pink-50 rounded-2xl p-5 border-2 border-red-300 shadow-lg">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-2">
                            <div className="bg-red-500 p-2 rounded-lg">
                              <Package className="text-white" size={18} />
                            </div>
                            <h3 className="font-black text-red-800 text-base uppercase tracking-wide">Despesas</h3>
                          </div>
                          <Button
                            size="sm"
                            onClick={() => addExpense(machineId)}
                            className="bg-red-600 hover:bg-red-700 text-white h-9 px-3 shadow-md hover:shadow-lg transition-all"
                          >
                            <Plus size={16} className="mr-1" />
                            Adicionar
                          </Button>
                        </div>
                        <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
                          {machine.expenses.map((expense, idx) => (
                            <div key={idx} className="flex gap-2 bg-white p-3 rounded-xl border border-red-200 hover:border-red-400 transition-all">
                              <Input
                                placeholder="Nome da despesa"
                                value={expense.name}
                                onChange={(e) => updateExpense(machineId, idx, 'name', e.target.value)}
                                className="text-sm font-medium border-red-200 focus:border-red-400"
                              />
                              <div className="relative">
                                <span className="absolute left-3 top-2.5 text-red-600 font-bold">R$</span>
                                <Input
                                  type="number"
                                  step="0.01"
                                  placeholder="0.00"
                                  value={expense.value || ''}
                                  onChange={(e) => updateExpense(machineId, idx, 'value', e.target.value)}
                                  className="w-28 text-sm font-bold pl-9 border-red-200 focus:border-red-400"
                                />
                              </div>
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => removeExpense(machineId, idx)}
                                className="text-red-500 hover:text-red-700 hover:bg-red-50 h-10 w-10"
                              >
                                <Trash2 size={18} />
                              </Button>
                            </div>
                          ))}
                          {machine.expenses.length === 0 && (
                            <div className="text-center py-8">
                              <div className="bg-red-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                                <Package className="text-red-600" size={28} />
                              </div>
                              <p className="text-gray-500 text-sm font-medium">Nenhuma despesa cadastrada</p>
                            </div>
                          )}
                        </div>
                        <div className="mt-4 pt-4 border-t-2 border-red-300 bg-red-100 -mx-5 -mb-5 px-5 py-3 rounded-b-2xl">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-bold text-red-800 uppercase">Subtotal Despesas:</span>
                            <span className="text-xl font-black text-red-700">R$ {totalExpensesM.toFixed(2)}</span>
                          </div>
                        </div>
                      </div>

                      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-5 border-2 border-blue-300 shadow-lg">
                        <div className="flex items-center gap-2 mb-4">
                          <div className="bg-blue-500 p-2 rounded-lg">
                            <Wrench className="text-white" size={18} />
                          </div>
                          <h3 className="font-black text-blue-800 text-base uppercase tracking-wide">Mão de Obra</h3>
                        </div>
                        <div className="bg-white p-6 rounded-xl border-2 border-blue-200">
                          <div className="relative">
                            <span className="absolute left-4 top-4 text-blue-600 font-black text-xl">R$</span>
                            <Input
                              type="number"
                              step="0.01"
                              placeholder="0.00"
                              value={machine.labor || ''}
                              onChange={(e) => updateMachine(machineId, { labor: parseFloat(e.target.value) || 0 })}
                              className="text-2xl font-black text-center pl-12 pr-4 h-16 border-2 border-blue-300 focus:border-blue-500"
                            />
                          </div>
                          <p className="text-xs text-blue-700 mt-3 text-center font-semibold uppercase tracking-wide">Valor total da mão de obra técnica</p>
                        </div>
                        <div className="mt-6 bg-gradient-to-r from-blue-100 to-indigo-100 p-4 rounded-xl border border-blue-200">
                          <div className="text-center">
                            <p className="text-xs text-blue-700 font-bold uppercase mb-2">Resumo Financeiro</p>
                            <div className="space-y-2">
                              <div className="flex justify-between text-sm">
                                <span className="text-gray-600 font-medium">Receita:</span>
                                <span className="font-bold text-green-600">+R$ {(totalServices + (machine.labor || 0)).toFixed(2)}</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span className="text-gray-600 font-medium">Despesas:</span>
                                <span className="font-bold text-red-600">-R$ {totalExpensesM.toFixed(2)}</span>
                              </div>
                              <div className="h-px bg-blue-300 my-2"></div>
                              <div className="flex justify-between">
                                <span className="text-blue-800 font-black uppercase text-sm">Lucro:</span>
                                <span className={`font-black text-lg ${machineTotal >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                  R$ {machineTotal.toFixed(2)}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>

        {machines.length === 0 && (
          <Card className="p-16 bg-white/95 backdrop-blur-sm border-2 border-dashed border-gray-300 hover:border-blue-400 transition-all">
            <div className="text-center">
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 w-24 h-24 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-2xl">
                <Calculator className="text-white" size={48} />
              </div>
              <p className="text-gray-600 text-2xl font-bold mb-2">Nenhuma máquina cadastrada</p>
              <p className="text-gray-500 mb-6">Comece adicionando sua primeira máquina ao sistema</p>
              <Button onClick={addMachine} className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-6 text-lg font-bold shadow-xl hover:shadow-2xl transition-all hover:scale-105">
                <Plus size={24} className="mr-2" />
                Adicionar Primeira Máquina
              </Button>
            </div>
          </Card>
        )}
      </div>
      
      {saving && (
        <div className="fixed bottom-6 right-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-3 border border-white/20 backdrop-blur-sm animate-pulse">
          <Loader2 className="animate-spin" size={20} />
          <span className="font-bold">Salvando automaticamente...</span>
        </div>
      )}
    </div>
  );
}
