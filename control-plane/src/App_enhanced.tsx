/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useMemo, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Terminal, 
  ShieldCheck, 
  Activity, 
  Database, 
  Search, 
  Copy, 
  Check, 
  AlertTriangle, 
  Server, 
  Cpu, 
  Layers, 
  Flame, 
  BookOpen, 
  HelpCircle, 
  Lock, 
  RefreshCw, 
  Play, 
  Wrench, 
  Layers3, 
  CheckCircle,
  Clock,
  ExternalLink,
  ChevronDown,
  Sparkles,
  Award,
  HardDrive,
  Network,
  Cloud,
  GitBranch,
  Zap
} from "lucide-react";

import metadata from "../metadata.json";
import { 
  commandsCatalog, 
  projectNodes, 
  securityRuleList, 
  integrationQA, 
  Command, 
  ProjectNode 
} from "./data";

// Types for better type safety
type TabType = "overview" | "commands" | "rfc002" | "integration";
type ModuleType = "all" | "ai" | "system" | "infra" | "wp" | "lab";

export default function App() {
  // Navigation state
  const [activeTab, setActiveTab] = useState<TabType>("overview");
  
  // Interactive commands state
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedModule, setSelectedModule] = useState<ModuleType>("all");
  const [copiedCommandId, setCopiedCommandId] = useState<string | null>(null);

  // System health toggles
  const [hostPostgres, setHostPostgres] = useState(true);
  const [dockerDaemon, setDockerDaemon] = useState(true);
  const [secureEnvPerms, setSecureEnvPerms] = useState(true);
  const [geminiApiKeySet, setGeminiApiKeySet] = useState(true);
  const [gitIgnoredSecrets, setGitIgnoredSecrets] = useState(true);
  const [localOllamaModel, setLocalOllamaModel] = useState(false);

  // Database inspector state
  const [selectedProjId, setSelectedProjId] = useState<string>("anaconda");

  // FAQ accordion state
  const [openFaqId, setOpenFaqId] = useState<number | null>(0);

  // System fix simulation state
  const [isFixing, setIsFixing] = useState(false);
  const [fixLogs, setFixLogs] = useState<string[]>([]);

  // Dynamic health score calculation
  const healthScore = useMemo(() => {
    const weights = {
      postgres: 20,
      docker: 20,
      envPerms: 20,
      geminiKey: 15,
      gitIgnore: 15,
      ollama: 10,
    };
    
    let score = 0;
    if (hostPostgres) score += weights.postgres;
    if (dockerDaemon) score += weights.docker;
    if (secureEnvPerms) score += weights.envPerms;
    if (geminiApiKeySet) score += weights.geminiKey;
    if (gitIgnoredSecrets) score += weights.gitIgnore;
    if (localOllamaModel) score += weights.ollama;
    
    return Math.min(score, 100);
  }, [hostPostgres, dockerDaemon, secureEnvPerms, geminiApiKeySet, gitIgnoredSecrets, localOllamaModel]);

  // Get health status message
  const healthStatus = useMemo(() => {
    if (healthScore >= 80) return { label: "Grado Producción", color: "emerald", icon: CheckCircle };
    if (healthScore >= 50) return { label: "Requiere Atención", color: "amber", icon: AlertTriangle };
    return { label: "Estado Crítico", color: "red", icon: AlertTriangle };
  }, [healthScore]);

  // Set document title dynamically
  useEffect(() => {
    document.title = `${metadata.name || "HPD CLI Core"} | Control Room`;
  }, []);

  // Copy command to clipboard
  const copyToClipboard = useCallback(async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedCommandId(id);
      setTimeout(() => setCopiedCommandId(null), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  }, []);

  // Simulate system fix execution
  const runSystemFix = useCallback(() => {
    if (isFixing || healthScore === 100) return;
    
    setIsFixing(true);
    setFixLogs(["🛠️ Iniciando pipeline de reparación: hpd system fix..."]);
    
    const steps = [
      { delay: 500, message: "✓ Verificando permisos en ~/.hpd/.env", action: () => setSecureEnvPerms(true) },
      { delay: 1100, message: "✓ Re-enlazando demonio de Docker host socket", action: () => setDockerDaemon(true) },
      { delay: 1700, message: "✓ Verificando base de datos PostgreSQL local", action: () => setHostPostgres(true) },
      { delay: 2200, message: "✓ Asegurando filtros Git y archivos ignorados", action: () => setGitIgnoredSecrets(true) },
      { delay: 2800, message: "✓ ¡Reparación completada! Health Score optimizado.", action: () => {} },
    ];
    
    steps.forEach(({ delay, message, action }) => {
      setTimeout(() => {
        setFixLogs(prev => [...prev, message]);
        action();
        if (message.includes("completada")) {
          setTimeout(() => setIsFixing(false), 500);
        }
      }, delay);
    });
  }, [isFixing, healthScore]);

  // Clear fix logs
  const clearFixLogs = useCallback(() => {
    setFixLogs([]);
  }, []);

  // Filter commands based on search and module
  const filteredCommands = useMemo(() => {
    return commandsCatalog.filter((cmd) => {
      const matchesSearch = 
        cmd.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        cmd.usage.toLowerCase().includes(searchTerm.toLowerCase()) ||
        cmd.description.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesModule = selectedModule === "all" || cmd.module === selectedModule;
      
      return matchesSearch && matchesModule;
    });
  }, [searchTerm, selectedModule]);

  // Get selected project details
  const selectedProject = useMemo(() => {
    return projectNodes.find(p => p.id === selectedProjId) || projectNodes[0];
  }, [selectedProjId]);

  // Module filter buttons configuration
  const moduleFilters: Array<{ id: ModuleType; label: string; icon: React.ElementType }> = [
    { id: "all", label: "Todos", icon: Terminal },
    { id: "ai", label: "hpd ai", icon: Sparkles },
    { id: "system", label: "hpd system", icon: Cpu },
    { id: "infra", label: "infra / db", icon: Database },
    { id: "wp", label: "wordpress", icon: Layers3 },
    { id: "lab", label: "hpd lab", icon: Flame },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#090d16] via-[#0a0f1a] to-[#0b101c] text-[#e2e8f0] font-sans selection:bg-[#00f2fe]/30 selection:text-[#00f2fe] antialiased">
      
      {/* Animated background grid */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#1f293708_1px,transparent_1px),linear-gradient(to_bottom,#1f293708_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />
      <div className="fixed top-0 left-1/4 w-96 h-96 bg-[#00f2fe]/5 blur-3xl rounded-full pointer-events-none animate-pulse" />
      <div className="fixed bottom-10 right-1/4 w-96 h-96 bg-[#4f46e5]/5 blur-3xl rounded-full pointer-events-none animate-pulse" style={{ animationDuration: "8s" }} />

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 relative z-10">
        
        {/* Header Section */}
        <header className="border border-slate-800/80 bg-slate-950/60 backdrop-blur-md rounded-2xl p-6 mb-8 shadow-2xl relative overflow-hidden transition-all duration-300 hover:border-slate-700/80">
          <div className="absolute top-0 right-0 h-1 sm:h-auto sm:w-1 bg-gradient-to-r sm:bg-gradient-to-b from-cyan-400 via-indigo-500 to-purple-500 w-full sm:bottom-0 rounded-r-2xl" />
          
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1.5 text-[10px] uppercase tracking-widest bg-emerald-500/10 text-emerald-400 font-mono px-2.5 py-1 rounded-full border border-emerald-500/20 shadow-[0_0_12px_rgba(16,185,129,0.15)]">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  HPD System Local Aware
                </span>
                <span className="inline-flex items-center gap-1.5 text-[10px] uppercase tracking-widest bg-slate-800/80 text-slate-300 font-mono px-2.5 py-1 rounded-full border border-slate-700">
                  <Award className="w-2.5 h-2.5 text-cyan-400" />
                  GitHub CI: Passing
                </span>
                <span className="inline-flex items-center gap-1.5 text-[10px] uppercase tracking-widest bg-indigo-500/10 text-indigo-400 font-mono px-2.5 py-1 rounded-full border border-indigo-500/20">
                  <GitBranch className="w-2.5 h-2.5" />
                  RFC-002 Compliant
                </span>
              </div>
              
              <h1 className="text-3xl sm:text-4xl font-display font-semibold bg-gradient-to-r from-white via-[#f1f5f9] to-slate-400 bg-clip-text text-transparent tracking-tight">
                {metadata.name || "HPD CLI Core Controller"}
              </h1>
              
              <p className="text-sm text-slate-400 max-w-2xl leading-relaxed">
                {metadata.description || "Interactive operations dashboard and workspace diagnostic portal."}
              </p>
            </div>

            {/* Health Score Panel */}
            <div className="flex items-center gap-4 bg-slate-900/90 border border-slate-800 p-4 rounded-xl min-w-[260px] shadow-inner backdrop-blur-sm">
              <div className="relative">
                <svg className="w-16 h-16 transform -rotate-90">
                  <circle cx="32" cy="32" r="28" className="stroke-slate-800 fill-none" strokeWidth="4" />
                  <circle 
                    cx="32" 
                    cy="32" 
                    r="28" 
                    className="stroke-[#00f2fe] fill-none transition-all duration-1000 ease-out" 
                    strokeWidth="4" 
                    strokeDasharray={2 * Math.PI * 28}
                    strokeDashoffset={2 * Math.PI * 28 * (1 - healthScore / 100)}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-lg font-bold text-white">{healthScore}%</span>
                </div>
              </div>
              <div className="flex-1">
                <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">System Health</div>
                <div className={`font-display font-semibold text-sm flex items-center gap-1.5 ${
                  healthStatus.color === "emerald" ? "text-emerald-400" : 
                  healthStatus.color === "amber" ? "text-amber-400" : "text-red-400"
                }`}>
                  {React.createElement(healthStatus.icon, { className: "w-3.5 h-3.5" })}
                  {healthStatus.label}
                </div>
                <div className="text-[9px] font-mono text-cyan-400/80 mt-1">47/47 Tests Verdes</div>
              </div>
            </div>
          </div>

          {/* Quick Stats Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-5 border-t border-slate-900/80 text-slate-400 text-xs font-mono">
            <div className="flex items-center gap-2 bg-slate-900/40 p-2.5 rounded-lg border border-slate-900 hover:border-slate-800 transition-colors">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              <span>Snapshot: <strong className="text-slate-200">2026-05-28</strong></span>
            </div>
            <div className="flex items-center gap-2 bg-slate-900/40 p-2.5 rounded-lg border border-slate-900 hover:border-slate-800 transition-colors">
              <GitBranch className="w-3.5 h-3.5 text-indigo-400" />
              <span>Version: <strong className="text-slate-200">v1.4.2 stable</strong></span>
            </div>
            <div className="flex items-center gap-2 bg-slate-900/40 p-2.5 rounded-lg border border-slate-900 hover:border-slate-800 transition-colors">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Denylist: <strong className="text-emerald-300">ACTIVA</strong></span>
            </div>
            <div className="flex items-center gap-2 bg-slate-900/40 p-2.5 rounded-lg border border-slate-900 hover:border-slate-800 transition-colors">
              <Database className="w-3.5 h-3.5 text-violet-400" />
              <span>Aislamiento DB: <strong className="text-violet-300">RFC-002 OK</strong></span>
            </div>
          </div>
        </header>

        {/* Navigation Tabs */}
        <div className="flex overflow-x-auto gap-1.5 p-1.5 bg-slate-950/80 border border-slate-800 rounded-xl mb-6 shadow-lg backdrop-blur-sm scrollbar-none">
          {[
            { id: "overview", label: "Integración Local & Doctor", icon: Cpu },
            { id: "commands", label: "Catálogo de Comandos", icon: Terminal },
            { id: "rfc002", label: "Bases de Datos (RFC-002)", icon: Database },
            { id: "integration", label: "Preguntas de Integrabilidad", icon: HelpCircle },
          ].map((tab) => (
            <button 
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-mono tracking-wider uppercase transition-all whitespace-nowrap ${
                activeTab === tab.id 
                  ? "bg-slate-800/80 text-[#00f2fe] border-b-2 border-cyan-400 font-bold shadow-sm" 
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Main Content */}
        <main className="min-h-[500px]">
          <AnimatePresence mode="wait">
            
            {/* Overview Tab */}
            {activeTab === "overview" && (
              <motion.div 
                key="overview"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                className="grid grid-cols-1 lg:grid-cols-3 gap-8"
              >
                {/* Left Column - System Diagnostics */}
                <div className="lg:col-span-2 space-y-8">
                  <div className="border border-slate-800 bg-slate-950/40 rounded-xl p-6 backdrop-blur-sm">
                    <div className="flex items-center gap-2 mb-5">
                      <Wrench className="w-5 h-5 text-cyan-400" />
                      <h2 className="text-lg font-display font-medium text-white">
                        Simulador de Diagnóstico: hpd-cli-core local
                      </h2>
                    </div>
                    
                    <p className="text-xs text-slate-400 mb-6 leading-relaxed">
                      El proyecto <strong className="text-slate-200">hpd-cli-core</strong> actúa como el plano de control para tu sistema local. 
                      Utiliza este panel interactivo para simular el estado de tu Host e infraestructura.
                    </p>

                    {/* Health Checkboxes Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {[
                        { id: "postgres", label: "PostgreSQL Local Activo", desc: "Habilita el despliegue del pool central y creación de esquemas.", checked: hostPostgres, setter: setHostPostgres },
                        { id: "docker", label: "Docker Daemon en Ejecución", desc: "Orquesta WordPress Docker y contenedores de datos ETL.", checked: dockerDaemon, setter: setDockerDaemon },
                        { id: "env", label: "Permisos Seguros de .env", desc: "Evita lectura no autorizada del config en el filesystem local.", checked: secureEnvPerms, setter: setSecureEnvPerms },
                        { id: "gemini", label: "GEMINI_API_KEY Configurada", desc: "Habilita el router inteligente para ask, scan, analyze y patch.", checked: geminiApiKeySet, setter: setGeminiApiKeySet },
                        { id: "git", label: "Filtros de Git e Ignore", desc: "Protege contraseñas locales contra exposiciones fortuitas.", checked: gitIgnoredSecrets, setter: setGitIgnoredSecrets },
                        { id: "ollama", label: "Ollama Fallback Local", desc: "Carga un LLM aislado localmente para operar sin conexión.", checked: localOllamaModel, setter: setLocalOllamaModel, badge: "Offline" },
                      ].map((item) => (
                        <div key={item.id} className="p-4 bg-slate-900/30 border border-slate-800 hover:border-slate-700 rounded-xl transition-all flex items-start gap-3 group">
                          <input 
                            type="checkbox" 
                            id={item.id}
                            checked={item.checked} 
                            onChange={(e) => item.setter(e.target.checked)}
                            className="mt-1 w-4 h-4 rounded text-cyan-600 bg-slate-950 border-slate-700 focus:ring-cyan-500 focus:ring-offset-0"
                          />
                          <div className="flex-1">
                            <label htmlFor={item.id} className="text-xs font-semibold text-slate-200 block cursor-pointer flex items-center gap-2">
                              {item.label}
                              {item.badge && (
                                <span className="bg-cyan-500/15 text-[9px] text-[#00f2fe] px-1.5 py-0.5 rounded font-mono">
                                  {item.badge}
                                </span>
                              )}
                            </label>
                            <span className="text-[10px] text-slate-400 leading-snug block mt-0.5">{item.desc}</span>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* System Fix Action */}
                    <div className="mt-6 pt-6 border-t border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                      <div>
                        <div className="text-xs text-slate-300 font-medium">¿Hay fallas detectadas en el sistema local?</div>
                        <div className="text-[10px] text-slate-400 mt-1">El CLI ofrece auto-corrección sin modificar destructivamente tus datos.</div>
                      </div>
                      <div className="flex gap-2">
                        {fixLogs.length > 0 && (
                          <button 
                            onClick={clearFixLogs}
                            className="text-xs text-slate-400 hover:text-slate-200 px-3 py-2 rounded-lg border border-slate-700 transition-colors"
                          >
                            Limpiar logs
                          </button>
                        )}
                        <button 
                          onClick={runSystemFix}
                          disabled={isFixing || healthScore === 100}
                          className={`font-mono text-xs uppercase tracking-wider px-5 py-2 rounded-lg flex items-center gap-2 transition-all ${
                            healthScore === 100 
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 cursor-not-allowed" 
                              : isFixing 
                                ? "bg-slate-800 text-[#00f2fe] border border-cyan-500/30 cursor-wait" 
                                : "bg-gradient-to-r from-cyan-500 to-cyan-600 text-slate-950 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)] hover:scale-[1.02] font-bold cursor-pointer"
                          }`}
                        >
                          {isFixing ? (
                            <>
                              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                              Aplicando fix...
                            </>
                          ) : healthScore === 100 ? (
                            <>
                              <CheckCircle className="w-3.5 h-3.5" />
                              Sistema Óptimo
                            </>
                          ) : (
                            <>
                              <Wrench className="w-3.5 h-3.5" />
                              Ejecutar system fix
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Fix Logs Console */}
                    <AnimatePresence>
                      {fixLogs.length > 0 && (
                        <motion.div 
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          className="mt-4 p-3 bg-slate-950 border border-slate-800 rounded-lg"
                        >
                          <div className="flex items-center gap-2 mb-2 justify-between">
                            <span className="text-[9px] font-mono uppercase text-slate-500 tracking-wider">CLI Buffer Output:</span>
                            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                          </div>
                          <div className="font-mono text-[10px] space-y-1 text-slate-300 max-h-32 overflow-y-auto">
                            {fixLogs.map((log, i) => (
                              <div key={i} className="flex gap-2">
                                <span className="text-slate-600 select-none">$</span>
                                <span className={log.startsWith("✓") ? "text-emerald-400" : "text-cyan-400"}>
                                  {log}
                                </span>
                              </div>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Recommendations Panel */}
                  <div className="border border-slate-800 bg-slate-950/20 rounded-xl p-6 backdrop-blur-sm">
                    <div className="flex items-center gap-2 mb-5">
                      <AlertTriangle className="w-5 h-5 text-amber-500" />
                      <h3 className="text-sm font-semibold text-slate-100">
                        Recomendaciones del Control Plane
                        {healthScore < 100 && <span className="text-amber-400 text-xs ml-2">({6 - Object.values({hostPostgres, dockerDaemon, secureEnvPerms, geminiApiKeySet, gitIgnoredSecrets, localOllamaModel}).filter(Boolean).length} alertas)</span>}
                      </h3>
                    </div>

                    <div className="space-y-3">
                      {healthScore === 100 ? (
                        <div className="p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-lg flex gap-3 text-xs text-slate-300 leading-relaxed">
                          <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                          <div>
                            ¡Tu entorno está completamente optimizado! No se detectaron fallos prioritarios. Has desplegado las capas de seguridad, Docker corre en perfectas condiciones y el Singleton local fluye de manera idónea.
                          </div>
                        </div>
                      ) : (
                        <>
                          {!hostPostgres && (
                            <div className="p-3 bg-red-950/20 border border-red-500/10 rounded-lg flex gap-3 text-xs leading-relaxed">
                              <span className="text-red-400 font-bold font-mono shrink-0">DB_FAIL:</span>
                              <div>PostgreSQL no responde localmente. Proyectos como <strong>Proyecto Anaconda</strong> u <strong>HPD WordPress</strong> fallarán.<br />
                                <code className="text-cyan-400 text-[10px] mt-1 inline-block">hpd system fix --apply</code>
                              </div>
                            </div>
                          )}
                          {!dockerDaemon && (
                            <div className="p-3 bg-red-950/20 border border-red-500/10 rounded-lg flex gap-3 text-xs leading-relaxed">
                              <span className="text-red-400 font-bold font-mono shrink-0">DOCKER_FAIL:</span>
                              <div>Demonio Docker desconectado. Imposible orquestar contenedores.<br />
                                <code className="text-cyan-400 text-[10px] mt-1 inline-block">service docker restart</code>
                              </div>
                            </div>
                          )}
                          {!secureEnvPerms && (
                            <div className="p-3 bg-amber-950/20 border border-amber-500/10 rounded-lg flex gap-3 text-xs leading-relaxed">
                              <span className="text-amber-400 font-bold font-mono shrink-0">SECURITY:</span>
                              <div>Permisos de lectura abiertos en `~/.hpd/.env`.<br />
                                <code className="text-cyan-400 text-[10px] mt-1 inline-block">chmod 600 ~/.hpd/.env</code>
                              </div>
                            </div>
                          )}
                          {!geminiApiKeySet && (
                            <div className="p-3 bg-amber-950/20 border border-amber-500/10 rounded-lg flex gap-3 text-xs leading-relaxed">
                              <span className="text-amber-400 font-bold font-mono shrink-0">AI_WARN:</span>
                              <div>API de Gemini desconectada. Las funciones inteligentes estarán deshabilitadas.</div>
                            </div>
                          )}
                          {!gitIgnoredSecrets && (
                            <div className="p-3 bg-indigo-950/20 border border-indigo-500/10 rounded-lg flex gap-3 text-xs leading-relaxed">
                              <span className="text-indigo-400 font-bold font-mono shrink-0">ENV_TRACK:</span>
                              <div>Se detectaron archivos `.env` en directorios activos. El sanitizador omitirá su carga.</div>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right Column - Security & Precheck */}
                <div className="space-y-8">
                  {/* Security Panel */}
                  <div className="border border-slate-800 bg-slate-950 rounded-xl p-6 relative overflow-hidden shadow-xl">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-400/5 rounded-full blur-2xl" />
                    
                    <div className="flex items-center gap-2 mb-5">
                      <ShieldCheck className="w-5 h-5 text-emerald-400" />
                      <h3 className="text-sm font-semibold text-white">Nivel de Hardening & Seguridad</h3>
                    </div>

                    <div className="space-y-4">
                      {securityRuleList.map((rule, idx) => (
                        <div key={idx} className="space-y-1">
                          <h4 className="text-[11px] font-mono text-cyan-400 flex items-center gap-1.5 uppercase font-semibold">
                            <span className="w-1 h-3 bg-cyan-400 inline-block rounded-sm" />
                            {rule.title}
                          </h4>
                          <p className="text-[11px] text-slate-400 leading-relaxed pl-2.5">
                            {rule.description}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Precheck Terminal */}
                  <div className="border border-slate-800 bg-slate-950/80 rounded-xl p-5 shadow-inner">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-300">
                        <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                        Host Precheck Terminal
                      </div>
                      <span className="text-[10px] uppercase font-mono tracking-widest text-cyan-400">v1.4</span>
                    </div>

                    <div className="font-mono text-[10px] bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-300 space-y-1.5">
                      <div className="text-slate-500 flex justify-between">
                        <span>$ hpd system serverize --precheck</span>
                        <span className="text-emerald-400">✓ Ready</span>
                      </div>
                      <div className="h-px bg-slate-800 my-2" />
                      <div className="flex justify-between"><span>CPU Diagnostics:</span><span className="text-slate-200">Ok (4 Cores)</span></div>
                      <div className="flex justify-between"><span>RAM Memory:</span><span className="text-slate-200">8.2 GB Total</span></div>
                      <div className="flex justify-between"><span>Storage (SWAP):</span><span className="text-slate-200">4.0 GB</span></div>
                      <div className="flex justify-between text-cyan-400"><span>CI Workflows:</span><span>47 Tests ✓</span></div>
                      <div className="flex justify-between text-emerald-400 pt-1 border-t border-slate-800 mt-1"><span>Status:</span><span>HEALTHY ({healthScore}%)</span></div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Commands Tab */}
            {activeTab === "commands" && (
              <motion.div 
                key="commands"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25 }}
                className="space-y-6"
              >
                {/* Search & Filter Bar */}
                <div className="border border-slate-800 bg-slate-950/60 p-6 rounded-xl shadow-md backdrop-blur-sm">
                  <div className="flex flex-col lg:flex-row gap-4 items-center justify-between">
                    <div className="w-full lg:w-96 relative">
                      <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                      <input 
                        type="text" 
                        placeholder="Buscar comando, uso o módulo..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full bg-slate-900/60 border border-slate-700 text-sm text-slate-200 rounded-xl pl-10 pr-4 py-2.5 focus:outline-none focus:border-cyan-400/80 focus:ring-1 focus:ring-cyan-400/20 transition-all placeholder-slate-500 font-mono"
                      />
                    </div>
                    
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-xs text-slate-400 mr-1 uppercase font-mono tracking-wider">Filtrar:</span>
                      {moduleFilters.map((mod) => {
                        const Icon = mod.icon;
                        return (
                          <button
                            key={mod.id}
                            onClick={() => setSelectedModule(mod.id)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all flex items-center gap-1.5 border ${
                              selectedModule === mod.id 
                                ? "bg-cyan-500/15 text-cyan-400 border-cyan-400 shadow-sm" 
                                : "bg-slate-900/40 text-slate-400 border-slate-700 hover:text-slate-200 hover:border-slate-600"
                            }`}
                          >
                            <Icon className="w-3 h-3" />
                            {mod.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Commands Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                  {filteredCommands.length > 0 ? (
                    filteredCommands.map((cmd, idx) => {
                      const commandKey = `${cmd.module}-${idx}`;
                      const moduleColor = {
                        ai: "from-cyan-500/20 to-cyan-600/5 border-cyan-500/20",
                        system: "from-amber-500/20 to-amber-600/5 border-amber-500/20",
                        infra: "from-violet-500/20 to-violet-600/5 border-violet-500/20",
                        wp: "from-blue-500/20 to-blue-600/5 border-blue-500/20",
                        lab: "from-rose-500/20 to-rose-600/5 border-rose-500/20",
                      }[cmd.module];
                      
                      return (
                        <div 
                          key={commandKey} 
                          className={`bg-gradient-to-br ${moduleColor} bg-slate-950/40 border rounded-xl p-5 shadow-xl transition-all hover:-translate-y-1 hover:shadow-2xl flex flex-col group relative overflow-hidden`}
                        >
                          <div className="space-y-2.5 flex-1">
                            <div className="flex justify-between items-start">
                              <span className={`text-[10px] font-mono px-2 py-0.5 rounded uppercase font-semibold border ${
                                cmd.module === "ai" ? "bg-cyan-950/40 text-cyan-400 border-cyan-500/20" :
                                cmd.module === "system" ? "bg-amber-950/30 text-amber-400 border-amber-500/20" :
                                cmd.module === "infra" ? "bg-violet-950/40 text-violet-400 border-violet-500/20" :
                                cmd.module === "wp" ? "bg-blue-950/40 text-blue-400 border-blue-500/20" :
                                "bg-rose-950/40 text-rose-400 border-rose-500/20"
                              }`}>
                                {cmd.module === "infra" ? "infrastructure" : `hpd ${cmd.module}`}
                              </span>
                              
                              <span className={`text-[9px] uppercase tracking-wider font-mono font-semibold flex items-center gap-1 ${
                                cmd.level === "Ready" ? "text-emerald-400" : 
                                cmd.level === "In Progress" ? "text-amber-400 animate-pulse" : "text-slate-500"
                              }`}>
                                <span className="w-1.5 h-1.5 rounded-full bg-current" />
                                {cmd.level}
                              </span>
                            </div>

                            <h3 className="text-base font-display font-medium text-slate-100 group-hover:text-white transition-colors flex items-center gap-2">
                              {cmd.name}
                              {cmd.safetyFilter && (
                                <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[9px] px-1.5 py-0.5 rounded font-mono flex items-center gap-0.5">
                                  <Lock className="w-2.5 h-2.5" />
                                  Hardened
                                </span>
                              )}
                            </h3>
                            
                            <p className="text-xs text-slate-400 leading-relaxed">
                              {cmd.description}
                            </p>
                          </div>

                          <div className="mt-5 pt-3 border-t border-slate-800/50">
                            <div className="p-2.5 bg-slate-950/80 rounded-lg border border-slate-800 flex items-center justify-between gap-3 text-xs text-slate-300 font-mono">
                              <code className="text-[11px] text-cyan-300 truncate">$ {cmd.usage}</code>
                              <button 
                                onClick={() => copyToClipboard(cmd.usage, commandKey)}
                                className="text-slate-500 hover:text-cyan-400 shrink-0 p-1 hover:bg-slate-800 rounded transition-colors"
                                title="Copiar comando"
                              >
                                {copiedCommandId === commandKey ? (
                                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                                ) : (
                                  <Copy className="w-3.5 h-3.5" />
                                )}
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="col-span-full py-16 text-center text-slate-500 border border-dashed border-slate-700 rounded-xl bg-slate-950/20 font-mono text-sm">
                      <Terminal className="w-10 h-10 text-slate-600 mx-auto mb-3 opacity-50" />
                      <p>Ningún comando coincide con los criterios de búsqueda</p>
                      <button 
                        onClick={() => { setSearchTerm(""); setSelectedModule("all"); }}
                        className="mt-3 text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
                      >
                        Limpiar filtros →
                      </button>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* RFC-002 Tab */}
            {activeTab === "rfc002" && (
              <motion.div 
                key="rfc002"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25 }}
                className="grid grid-cols-1 lg:grid-cols-3 gap-8"
              >
                {/* Project Selector */}
                <div className="lg:col-span-1 space-y-4">
                  <div className="border border-slate-800 bg-slate-950 p-5 rounded-xl shadow-md">
                    <h3 className="text-sm font-mono uppercase tracking-wider text-cyan-400 mb-2">RFC-002 Database Isolation</h3>
                    <p className="text-xs text-slate-400 leading-relaxed mb-5">
                      Principio de aislamiento: Instancia central PostgreSQL con bases de datos aisladas y roles-propietario exclusivos por proyecto.
                    </p>

                    <div className="space-y-2">
                      {projectNodes.map((node) => (
                        <button
                          key={node.id}
                          onClick={() => setSelectedProjId(node.id)}
                          className={`w-full text-left p-3.5 rounded-lg border transition-all flex items-center justify-between ${
                            selectedProjId === node.id 
                              ? "bg-slate-800/60 border-cyan-400/60 shadow-[0_0_12px_rgba(6,182,212,0.15)]" 
                              : "bg-slate-950 border-slate-800 hover:border-slate-700 hover:bg-slate-900/50"
                          }`}
                        >
                          <div>
                            <div className="text-xs font-semibold text-slate-200">{node.name}</div>
                            <div className="text-[10px] font-mono text-slate-400 mt-0.5">{node.type}</div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${
                              node.status === "Active" ? "bg-emerald-400 shadow-sm shadow-emerald-400/30" : "bg-amber-400"
                            }`} />
                            <span className="text-[9px] font-mono uppercase text-slate-500">{node.status}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Database Details */}
                <div className="lg:col-span-2 space-y-6">
                  <div className="border border-slate-800 bg-slate-950 p-6 rounded-xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/5 rounded-full blur-3xl" />
                    
                    <div className="space-y-6">
                      <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
                        <Database className="w-5 h-5 text-indigo-400" />
                        <div>
                          <h4 className="text-sm font-semibold text-white">Inspeccionar Aislamiento: {selectedProject.name}</h4>
                          <span className="text-[10px] text-slate-400 font-mono">Topología lógica PostgreSQL virtualizada</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        {/* Host Instance */}
                        <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-xl">
                          <div className="flex items-center gap-2 mb-3">
                            <Server className="w-4 h-4 text-cyan-400" />
                            <span className="text-xs font-mono font-semibold text-slate-200">Postgres Instance</span>
                          </div>
                          <div className="space-y-2 text-[11px] font-mono">
                            <div className="flex justify-between"><span className="text-slate-400">Host:</span><span className="text-slate-200">127.0.0.1 (Docker)</span></div>
                            <div className="flex justify-between"><span className="text-slate-400">Engine:</span><span className="text-slate-200">PostgreSQL v15</span></div>
                            <div className="flex justify-between"><span className="text-slate-400">Port:</span><span className="text-cyan-400">5432 (Internal)</span></div>
                          </div>
                        </div>

                        {/* Isolated DB */}
                        <div className="bg-indigo-500/5 border border-indigo-500/15 p-4 rounded-xl">
                          <div className="flex items-center gap-2 mb-3">
                            <Layers className="w-4 h-4 text-indigo-400" />
                            <span className="text-xs font-mono font-semibold text-indigo-300">Database Aislada (RFC-002)</span>
                          </div>
                          <div className="space-y-2 text-[11px] font-mono">
                            <div className="flex justify-between"><span className="text-slate-400">Schema:</span><span className="text-white font-semibold">{selectedProject.dbName}</span></div>
                            <div className="flex justify-between"><span className="text-slate-400">Owner:</span><span className="text-white">{selectedProject.dbUser}</span></div>
                            <div className="flex justify-between"><span className="text-slate-400">Backup:</span><span className="text-cyan-400">pg_dump aislado</span></div>
                          </div>
                        </div>
                      </div>

                      {/* Connection Map */}
                      <div className="bg-slate-900/30 border border-slate-800 rounded-xl p-4">
                        <div className="text-[11px] uppercase tracking-wider font-mono text-slate-400 mb-3 flex items-center gap-1">
                          <Network className="w-3.5 h-3.5" />
                          Mapa de Conexión del Proyecto
                        </div>
                        
                        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-3 font-mono text-xs">
                          <div className="bg-slate-800 p-2.5 rounded border border-slate-700 w-full sm:w-auto text-center font-bold text-slate-200">
                            {selectedProject.name}
                          </div>
                          <div className="text-slate-500 flex items-center gap-2 text-[10px]">
                            <span>→</span>
                            <code className="text-cyan-400 bg-slate-900 px-2 py-1 rounded">credentials: {selectedProject.dbUser}</code>
                            <span>→</span>
                          </div>
                          <div className="bg-indigo-500/10 border border-indigo-500/20 p-2.5 rounded w-full sm:w-auto text-center font-bold text-indigo-300">
                            {selectedProject.dbName}
                          </div>
                        </div>
                      </div>

                      <p className="text-[11px] text-slate-400 leading-relaxed bg-slate-900/20 p-3 rounded-lg border border-slate-800">
                        <strong className="text-slate-300">Descripción:</strong> {selectedProject.description} Las contraseñas se almacenan de manera independiente en variables de entorno, con backups diarios automatizados ejecutando <code className="text-cyan-300 font-mono text-[10px]">pg_dump</code> exclusivamente sobre este esquema.
                      </p>
                    </div>

                    <div className="mt-5 pt-4 border-t border-slate-800 flex justify-between items-center text-[10px] font-mono text-slate-500">
                      <span>Provisión: <code className="text-cyan-400">hpd db provision {selectedProject.id}</code></span>
                      <span className="text-indigo-400">RFC-002 Compliant ✓</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Integration FAQs Tab */}
            {activeTab === "integration" && (
              <motion.div 
                key="integration"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25 }}
                className="grid grid-cols-1 lg:grid-cols-3 gap-8"
              >
                {/* Maturity Card */}
                <div className="lg:col-span-1 space-y-6">
                  <div className="border border-slate-800 bg-slate-950 p-6 rounded-xl shadow-md relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-xl" />
                    
                    <span className="text-[10px] font-mono uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full inline-block mb-3">
                      Grado de Producción
                    </span>
                    
                    <h3 className="text-lg font-display font-medium text-white mb-2">Madurez Local Stable</h3>
                    
                    <p className="text-xs text-slate-400 leading-relaxed mb-5">
                      El CLI local <strong className="text-slate-300">hpd-cli-core</strong> ha completado la fase de endurecimiento técnico (Hardening) logrando máxima resiliencia.
                    </p>

                    <div className="space-y-3 font-mono text-xs">
                      <div className="flex justify-between border-b border-slate-800 pb-2"><span>Cobertura Tests:</span><span className="text-emerald-400 font-bold">100% (47/47)</span></div>
                      <div className="flex justify-between border-b border-slate-800 pb-2"><span>CI Workflows:</span><span className="text-emerald-400 flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Passing</span></div>
                      <div className="flex justify-between border-b border-slate-800 pb-2"><span>Singleton AIRouter:</span><span className="text-cyan-400 font-bold">Activo</span></div>
                      <div className="flex justify-between border-b border-slate-800 pb-2"><span>Denylist Security:</span><span className="text-emerald-400 font-bold">Activo</span></div>
                      <div className="flex justify-between"><span>Licencia:</span><span className="text-slate-400">Apache-2.0</span></div>
                    </div>
                  </div>

                  {/* Quick Install */}
                  <div className="p-5 bg-indigo-500/5 border border-indigo-500/10 rounded-xl">
                    <div className="flex gap-2 text-indigo-300 font-mono text-xs uppercase tracking-wide mb-2 items-center">
                      <Zap className="w-4 h-4" />
                      Instalación Rápida
                    </div>
                    <code className="text-[11px] font-mono text-cyan-300 block bg-slate-950 p-2.5 rounded border border-slate-800">
                      $ pip install -e ".[dev]"
                    </code>
                    <p className="text-[10px] text-slate-400 leading-normal mt-2">
                      Monta el paquete CLI central de manera editable, enlazando todos los subparsers dinámicamente.
                    </p>
                  </div>
                </div>

                {/* FAQs Accordion */}
                <div className="lg:col-span-2">
                  <div className="border border-slate-800 bg-slate-950 p-6 rounded-xl shadow-md">
                    <h3 className="text-base font-display font-medium text-white mb-2 flex items-center gap-2">
                      <HelpCircle className="w-4 h-4 text-cyan-400" />
                      Detalles de Integrabilidad
                    </h3>
                    <p className="text-xs text-slate-400 leading-relaxed mb-6">
                      Revisa los detalles técnicos sobre el nivel de integración del sistema y los subproyectos del portafolio.
                    </p>

                    <div className="space-y-3">
                      {integrationQA.map((faq, idx) => (
                        <div 
                          key={idx} 
                          className="border border-slate-800 rounded-lg overflow-hidden bg-slate-900/20"
                        >
                          <button 
                            onClick={() => setOpenFaqId(openFaqId === idx ? null : idx)}
                            className="w-full text-left p-4 flex justify-between items-center bg-slate-950/40 hover:bg-slate-900/60 transition-colors"
                          >
                            <span className="text-xs font-semibold text-slate-200 pr-4">{faq.q}</span>
                            <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform duration-200 ${openFaqId === idx ? "rotate-180" : ""}`} />
                          </button>
                          
                          <AnimatePresence>
                            {openFaqId === idx && (
                              <motion.div 
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                exit={{ opacity: 0, height: 0 }}
                                transition={{ duration: 0.2 }}
                                className="overflow-hidden border-t border-slate-800"
                              >
                                <div className="p-4 text-xs text-slate-400 leading-relaxed bg-slate-900/30">
                                  {faq.a}
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

          </AnimatePresence>
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800 mt-12 pt-6 flex flex-col sm:flex-row justify-between items-center gap-4 text-[11px] font-mono text-slate-500">
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5" />
            <span>HPD CLI Control Plane Interactive Console © 2026</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="hover:text-cyan-400 cursor-help flex items-center gap-1">
              <Database className="w-3 h-3" /> RFC-002 Compliant
            </span>
            <span>|</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <Activity className="w-3 h-3" /> STATUS: EXCELENTE
            </span>
          </div>
        </footer>
      </div>
    </div>
  );
}
