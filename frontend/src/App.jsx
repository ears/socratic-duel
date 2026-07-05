import { useState, useEffect } from 'react';

const LENSES = [
  { id: 'empiricist', name: 'The Empiricist', description: 'Requires strict empirical evidence and data-driven validation. Rejects unfalsifiable claims.', icon: '🔬' },
  { id: 'systems_theorist', name: 'The Systems Theorist', description: 'Evaluates the thesis through complex interactions, feedback loops, and holistic consequences.', icon: '🕸️' },
  { id: 'ethicist', name: 'The Ethicist', description: 'Analyzes moral implications, human rights impact, and fairness of the proposed arguments.', icon: '⚖️' },
  { id: 'historian', name: 'The Historian', description: 'Contextualizes the thesis within historical precedents and long-term societal trends.', icon: '📜' },
  { id: 'pragmatist', name: 'The Pragmatist', description: 'Focuses on actionable outcomes, feasibility, and real-world utility over theoretical perfection.', icon: '⚙️' },
  { id: 'skeptic', name: 'The Skeptic', description: 'Actively tries to dismantle the thesis by exposing logical fallacies, biases, and weak assumptions.', icon: '🤔' },
  { id: 'economist', name: 'The Economist', description: 'Assesses cost-benefit ratios, resource allocation, and market dynamics surrounding the thesis.', icon: '📈' },
  { id: 'phenomenologist', name: 'The Phenomenologist', description: 'Examines the subjective, lived human experience and qualitative impacts of the thesis.', icon: '👁️' }
];

function App() {
  const [theme, setTheme] = useState('dark');
  const [thesis, setThesis] = useState('');
  const [phase, setPhase] = useState('input'); // input -> triage -> debate
  const [selectedLens, setSelectedLens] = useState(null);

  useEffect(() => {
    if (theme === 'dark') document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  }, [theme]);

  const toggleTheme = () => setTheme(theme === 'dark' ? 'light' : 'dark');

  const startDebate = () => {
    if (!selectedLens) return;
    setPhase('debate');
  };

  return (
    <div className="min-h-screen bg-[var(--bg-color)] text-[var(--text-color)] font-sans transition-colors duration-300">
      {/* Header */}
      <header className="border-b border-[var(--border-color)] bg-[var(--card-bg)]/80 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-white font-bold shadow-lg">
              ES
            </div>
            <h1 className="text-xl font-bold tracking-tight">
              Epistemic Synthesizer
            </h1>
          </div>
          <button 
            onClick={toggleTheme} 
            className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition flex items-center justify-center w-10 h-10"
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-16">
        
        {/* Phase 1: Input */}
        {phase === 'input' && (
          <div className="max-w-3xl mx-auto space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="text-center space-y-4">
              <div className="inline-block px-4 py-1.5 rounded-full border border-violet-500/30 bg-violet-500/10 text-violet-600 dark:text-violet-400 font-medium text-sm mb-4">
                Phase 1: Thesis Triage
              </div>
              <h2 className="text-5xl font-extrabold tracking-tight">Propose your Thesis</h2>
              <p className="text-xl opacity-70 leading-relaxed">
                Enter an argument to be rigorously stress-tested by a specialized AI dialectic loop.
              </p>
            </div>
            
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-violet-600 to-indigo-600 rounded-3xl blur opacity-25 group-hover:opacity-40 transition duration-500"></div>
              <textarea 
                className="relative w-full h-56 p-8 rounded-3xl bg-[var(--card-bg)] border border-[var(--border-color)] focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none text-lg shadow-xl leading-relaxed"
                placeholder="e.g., Artificial Intelligence will inevitably lead to a post-scarcity economy, rendering traditional capitalism obsolete..."
                value={thesis}
                onChange={e => setThesis(e.target.value)}
              />
            </div>
            
            <div className="flex justify-end">
              <button 
                onClick={() => setPhase('triage')}
                disabled={!thesis.trim()}
                className="px-8 py-4 bg-violet-600 hover:bg-violet-700 text-white font-semibold rounded-2xl shadow-lg shadow-violet-600/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed transform hover:-translate-y-1 active:translate-y-0 text-lg flex items-center gap-2"
              >
                Analyze & Triage <span className="text-xl">→</span>
              </button>
            </div>
          </div>
        )}

        {/* Phase 2: HITL Lens Selection */}
        {phase === 'triage' && (
          <div className="space-y-12 animate-in fade-in zoom-in-95 duration-500">
            <div className="text-center space-y-4 max-w-3xl mx-auto">
              <h2 className="text-4xl font-extrabold tracking-tight">Select an Epistemic Lens</h2>
              <p className="text-lg opacity-70">
                The triage agent has analyzed your thesis. Choose the academic framework that will drive the dialectical debate.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-[var(--card-bg)] border border-[var(--border-color)] shadow-sm max-w-4xl mx-auto">
              <h3 className="text-sm font-bold uppercase tracking-wider opacity-50 mb-3">Your Thesis</h3>
              <p className="text-lg italic border-l-4 border-violet-500 pl-4 py-1">{thesis}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {LENSES.map(lens => (
                <div 
                  key={lens.id}
                  onClick={() => setSelectedLens(lens.id)}
                  className={`relative p-6 rounded-3xl border-2 cursor-pointer transition-all duration-300 overflow-hidden ${
                    selectedLens === lens.id 
                      ? 'border-violet-500 bg-violet-500/5 shadow-xl shadow-violet-500/10' 
                      : 'border-[var(--border-color)] bg-[var(--card-bg)] hover:border-violet-500/50 hover:shadow-lg'
                  }`}
                >
                  {selectedLens === lens.id && (
                    <div className="absolute top-0 left-0 w-full h-1 bg-violet-500"></div>
                  )}
                  <div className="text-4xl mb-4">{lens.icon}</div>
                  <h3 className="text-xl font-bold mb-2">{lens.name}</h3>
                  <p className="opacity-70 text-sm leading-relaxed">{lens.description}</p>
                  
                  {/* Selection Indicator */}
                  <div className={`mt-6 h-8 rounded-lg flex items-center justify-center font-medium text-sm transition-colors ${
                    selectedLens === lens.id 
                      ? 'bg-violet-600 text-white' 
                      : 'bg-[var(--border-color)]/50 text-[var(--text-color)]/70'
                  }`}>
                    {selectedLens === lens.id ? 'Selected' : 'Select'}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-center mt-12 pt-8 border-t border-[var(--border-color)]">
              <button 
                onClick={startDebate}
                disabled={!selectedLens}
                className="px-12 py-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-2xl shadow-xl shadow-indigo-600/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 active:scale-95 text-lg"
              >
                Initialize Dialectical Loop
              </button>
            </div>
          </div>
        )}

        {/* Phase 3: Debate State (Placeholder for now) */}
        {phase === 'debate' && (
          <div className="max-w-4xl mx-auto text-center space-y-8 animate-in fade-in duration-1000 pt-16">
            <div className="relative inline-block">
              <div className="w-24 h-24 border-4 border-violet-500/30 border-t-violet-500 rounded-full animate-spin mx-auto"></div>
              <div className="absolute inset-0 flex items-center justify-center text-3xl">⚔️</div>
            </div>
            <h2 className="text-4xl font-extrabold">Debate Pipeline Active</h2>
            <p className="text-xl opacity-70">
              The {LENSES.find(l => l.id === selectedLens)?.name} is currently stress-testing your thesis.<br/>
              Awaiting final synthesized report...
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
