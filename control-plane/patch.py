import sys

with open('src/App_enhanced.tsx', 'r') as f:
    content = f.read()

auth_state_code = """
  const [authToken, setAuthToken] = useState(() => localStorage.getItem("hpd_token") || "");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authError, setAuthError] = useState("");

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem("hpd_token", authToken);
    checkHealth(authToken);
  };

  const checkHealth = useCallback((token: string) => {
    fetch("http://localhost:8000/api/system/health", {
      headers: { "X-HPD-Token": token }
    })
      .then(res => {
        if (res.status === 401) {
          setIsAuthenticated(false);
          setAuthError("Token de acceso inválido");
          throw new Error("Unauthorized");
        }
        return res.json();
      })
      .then(data => {
        setIsAuthenticated(true);
        setAuthError("");
        if (data.hostPostgres !== undefined) setHostPostgres(data.hostPostgres);
        if (data.dockerDaemon !== undefined) setDockerDaemon(data.dockerDaemon);
        if (data.secureEnvPerms !== undefined) setSecureEnvPerms(data.secureEnvPerms);
        if (data.geminiApiKeySet !== undefined) setGeminiApiKeySet(data.geminiApiKeySet);
        if (data.gitIgnoredSecrets !== undefined) setGitIgnoredSecrets(data.gitIgnoredSecrets);
        if (data.localOllamaModel !== undefined) setLocalOllamaModel(data.localOllamaModel);
      })
      .catch(err => console.error("Error fetching health data:", err));
  }, []);

  useEffect(() => {
    if (authToken) {
      checkHealth(authToken);
    }
  }, [authToken, checkHealth]);

"""

lock_screen_code = """
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#090d16] flex flex-col items-center justify-center p-4 font-sans selection:bg-[#00f2fe]/30 selection:text-[#00f2fe]">
        <div className="fixed inset-0 bg-[linear-gradient(to_right,#1f293708_1px,transparent_1px),linear-gradient(to_bottom,#1f293708_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />
        <div className="fixed top-0 left-1/4 w-96 h-96 bg-[#00f2fe]/5 blur-3xl rounded-full pointer-events-none animate-pulse" />
        
        <div className="max-w-md w-full bg-slate-900/80 backdrop-blur-md border border-slate-800 p-8 rounded-2xl shadow-2xl text-center relative overflow-hidden z-10">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 to-indigo-500"></div>
          <Lock className="w-12 h-12 text-cyan-400 mx-auto mb-4" />
          <h2 className="text-2xl font-display font-medium text-white mb-2">HPD Control Plane</h2>
          <p className="text-slate-400 text-sm mb-6">Ingresa tu Token de Acceso para continuar</p>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <input 
                type="password" 
                placeholder="X-HPD-Token..."
                value={authToken}
                onChange={(e) => setAuthToken(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-500 text-center font-mono transition-colors"
              />
              {authError && <p className="text-rose-500 text-xs mt-2">{authError}</p>}
            </div>
            <button 
              type="submit"
              className="w-full bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-400 hover:to-cyan-500 text-slate-900 font-bold py-3 rounded-lg transition-all flex justify-center items-center gap-2 shadow-[0_0_15px_rgba(6,182,212,0.3)] hover:scale-[1.02]"
            >
              Desbloquear Control Plane
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
"""

# Insert auth state after setLocalOllamaModel
split1 = content.find("const [localOllamaModel, setLocalOllamaModel] = useState(false);")
if split1 != -1:
    end_of_line = content.find("\n", split1) + 1
    content = content[:end_of_line] + auth_state_code + content[end_of_line:]

# Insert lock screen before final return
split2 = content.find("  return (\n    <div className=\"min-h-screen")
if split2 != -1:
    content = content[:split2] + lock_screen_code + content[split2 + len("  return (\n"):]

with open('src/App.tsx', 'w') as f:
    f.write(content)
