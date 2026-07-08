import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

// Must match the exact order in the backend prompt (1-8)
const LENSES = [
  { id: 'empiricist', name: 'The Empiricist', description: 'Focuses on observable data, evidence, and rigorous testing.', icon: '🔬' },
  { id: 'rationalist', name: 'The Rationalist', description: 'Focuses on logical consistency, theoretical frameworks, and first principles.', icon: '🧠' },
  { id: 'hermeneut', name: 'The Hermeneut', description: 'Focuses on meaning, context, interpretation, and underlying narratives.', icon: '📖' },
  { id: 'pragmatist', name: 'The Engineer / Pragmatist', description: 'Focuses on practical utility, problem-solving, and implementation.', icon: '⚙️' },
  { id: 'ethicist', name: 'The Ethicist', description: 'Focuses on moral implications, values, fairness, and human impact.', icon: '⚖️' },
  { id: 'cognitive', name: 'The Cognitive Scientist', description: 'Focuses on human cognition, biases, mental models, and perception.', icon: '👁️' },
  { id: 'discourse', name: 'The Discourse Analyst', description: 'Focuses on power dynamics, rhetoric, ideology, and framing.', icon: '🗣️' },
  { id: 'systems', name: 'The Systems Theorist', description: 'Focuses on complex interactions, feedback loops, and holistic structures.', icon: '🕸️' }
];

function App() {
  const [theme, setTheme] = useState('light');
  const [thesis, setThesis] = useState('');
  const [targetAudience, setTargetAudience] = useState('Level 1 (15-year-old)');
  const [phase, setPhase] = useState('input'); // input -> triage_loading -> triage -> debate
  const [selectedLensIndex, setSelectedLensIndex] = useState(null);
  const [sessionId, setSessionId] = useState(() => Math.random().toString(36).substring(7));
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [currentActivity, setCurrentActivity] = useState('');
  const [errorMessage, setErrorMessage] = useState(null);
  const [triageResultText, setTriageResultText] = useState("");
  const [triageRejected, setTriageRejected] = useState(false);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    if (theme === 'dark') document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  }, [theme]);

  const toggleTheme = () => setTheme(theme === 'dark' ? 'light' : 'dark');

  const analyzeTriage = () => {
    if (!thesis.trim()) return;
    setPhase('triage_loading');
    setErrorMessage(null);
    setTriageResultText("");
    setTriageRejected(false);
    
    let localContent = "";
    
    // Call backend to trigger Phase 1 Triage
    const payload = `[Target Audience: ${targetAudience}]\n\n${thesis}`;
    const es = new EventSource(`/api/chat?session_id=${sessionId}&message=${encodeURIComponent(payload)}`);
    eventSourceRef.current = es;
    
    es.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.error) {
            setErrorMessage(`Phase 1 Error: ${data.error}`);
            setPhase('input');
            es.close();
            return;
        }
        if (data.content) {
            localContent += data.content;
            if (localContent.includes("[STATUS: REJECTED]")) {
                setTriageRejected(true);
            }
            setTriageResultText(prev => prev + data.content.replace("[STATUS: REJECTED]", ""));
        }
    };
    
    es.onerror = () => {
        es.close();
        // If we didn't hit an error payload, move to choice UI
        setPhase(prev => prev === 'triage_loading' ? 'triage' : prev);
    };
  };

  const startDebate = (lensIndex, isResume = false) => {
    const targetIndex = lensIndex !== undefined ? lensIndex : selectedLensIndex;
    if (targetIndex === null) return;
    
    setSelectedLensIndex(targetIndex);
    setPhase('debate');
    setIsTyping(true);
    setCurrentActivity(isResume ? 'Resuming connection...' : 'Initializing debate...');
    setErrorMessage(null);
    
    // Send the chosen number (1-8) to the backend to start, OR empty string if resuming connection
    const payload = isResume ? "" : (targetIndex + 1);
    const es = new EventSource(`/api/chat?session_id=${sessionId}&message=${payload}`);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.error) {
          setErrorMessage(`Phase 2 Error: ${data.error}`);
          setIsTyping(false);
          es.close();
          return;
      }

      if (data.keepalive) {
        const statuses = [
          "Still thinking...",
          "Connecting synapses...",
          "Consulting the digital oracle...",
          "Brewing some coffee...",
          "Reticulating splines...",
          "Pondering the infinite...",
          "Cross-referencing human history...",
          "Navigating the latent space..."
        ];
        setCurrentActivity(statuses[Math.floor(Math.random() * statuses.length)]);
        return;
      }
      
      if (data.status === 'complete') {
        setIsTyping(false);
        es.close();
        return;
      }
      
      if (data.author) {
        let statusText = "Thinking...";
        if (data.author === 'protagonist') statusText = "Formulating argument...";
        if (data.author === 'antagonist') statusText = "Preparing counter-argument...";
        if (data.author === 'judge') statusText = "Evaluating debate progress...";
        if (data.author.startsWith('citation_checker')) statusText = "Verifying citations...";
        if (data.author === 'synthesizer') statusText = "Synthesizing final report...";
        if (data.tool_calls && data.tool_calls.length > 0) {
          const tool = data.tool_calls[0].name;
          if (tool === 'search_semantic_scholar') statusText = "Searching academic papers...";
          if (tool === 'verify_url_status') statusText = "Checking reference link...";
        }
        setCurrentActivity(statusText);
      }

      if (data.content && data.content.trim() !== "") {
        setMessages(prev => {
          if (data.updated_draft) {
            const targetAuthor = data.author === 'citation_checker_proto' ? 'protagonist' : 'antagonist';
            const newMessages = [...prev];
            for (let i = newMessages.length - 1; i >= 0; i--) {
              if (newMessages[i].author === targetAuthor) {
                newMessages[i] = { ...newMessages[i], content: data.updated_draft };
                break;
              }
            }
            return [...newMessages, data];
          }
          return [...prev, data];
        });
      }
    };

    es.onerror = () => {
      es.close();
      setErrorMessage("Google's AI service is currently overloaded by high demand. Please refresh the page and try again!");
      setIsTyping(false);
    };
  };

  return (
    <div className="min-h-screen bg-[var(--bg-color)] text-[var(--text-color)] font-sans transition-colors duration-300">
      <header className="border-b border-[var(--border-color)] bg-[var(--card-bg)]/80 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <button 
            onClick={() => {
              setPhase('input');
              setThesis('');
              setSelectedLensIndex(null);
              setMessages([]);
              setSessionId(Math.random().toString(36).substring(7));
            }}
            className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer text-left"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-white font-bold shadow-lg">
              SD
            </div>
            <h1 className="text-xl font-bold tracking-tight">Socratic Duel</h1>
          </button>
          <button onClick={toggleTheme} className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition flex items-center justify-center w-10 h-10">
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-16">
        
        {errorMessage && (
          <div className="max-w-3xl mx-auto mb-8 p-6 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-800 rounded-2xl text-red-700 dark:text-red-400 font-bold shadow-lg flex justify-between items-center">
            <div>🚨 Backend Error: {errorMessage}</div>
            {phase === 'debate' && !errorMessage.includes('Automatically reconnecting') && (
              <button 
                onClick={() => startDebate(selectedLensIndex, true)} 
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition whitespace-nowrap ml-4 shadow"
              >
                Resume Connection
              </button>
            )}
          </div>
        )}
        
        {phase === 'input' && (
          <div className="max-w-3xl mx-auto space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="text-center space-y-4">
              <div className="inline-block px-4 py-1.5 rounded-full border border-violet-500/30 bg-violet-500/10 text-violet-600 dark:text-violet-400 font-medium text-sm mb-4">
                Phase 1: Thesis Triage
              </div>
              <h2 className="text-5xl font-extrabold tracking-tight">Propose your Thesis</h2>
              <p className="text-xl opacity-70 leading-relaxed">
                Enter an argument to be rigorously stress-tested by two intellectual black belts.
              </p>
            </div>
            
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-violet-600 to-indigo-600 rounded-3xl blur opacity-25 group-hover:opacity-40 transition duration-500"></div>
              <textarea 
                className="relative w-full h-56 p-8 rounded-3xl bg-[var(--card-bg)] border border-[var(--border-color)] focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none text-lg shadow-xl leading-relaxed"
                placeholder="e.g., Artificial Intelligence will inevitably lead to a post-scarcity economy..."
                value={thesis}
                onChange={e => setThesis(e.target.value)}
              />
            </div>
            
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
              <div className="flex items-center gap-3 w-full sm:w-auto">
                <label className="text-sm font-semibold opacity-70 whitespace-nowrap">Cognitive Complexity:</label>
                <select 
                  className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 flex-grow"
                  value={targetAudience}
                  onChange={(e) => setTargetAudience(e.target.value)}
                >
                  <option value="Level 1 (15-year-old)">Level 1 (15-year-old)</option>
                  <option value="Level 2 (Average Adult)">Level 2 (Average Adult)</option>
                  <option value="Level 3 (Average Academic)">Level 3 (Average Academic)</option>
                  <option value="Level 4 (PhD-Level)">Level 4 (PhD-Level)</option>
                </select>
              </div>
              <button 
                onClick={analyzeTriage}
                disabled={!thesis.trim()}
                className="px-8 py-4 bg-violet-600 hover:bg-violet-700 text-white font-semibold rounded-2xl shadow-lg shadow-violet-600/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed transform hover:-translate-y-1 active:translate-y-0 text-lg flex items-center gap-2"
              >
                Analyze & Triage <span className="text-xl">→</span>
              </button>
            </div>
          </div>
        )}

        {phase === 'triage_loading' && (
          <div className="max-w-4xl mx-auto text-center space-y-8 animate-in fade-in pt-16">
             <div className="w-16 h-16 border-4 border-violet-500/30 border-t-violet-500 rounded-full animate-spin mx-auto"></div>
             <h2 className="text-3xl font-extrabold">Triaging Thesis...</h2>
             <p className="text-lg opacity-70">The Orchestrator is analyzing your thesis and establishing context via Google Search.</p>
             <p className="text-md font-semibold text-violet-600 dark:text-violet-400 mt-6 animate-pulse">
               A little patience, please. Gemini’s gears are turning for you...
             </p>
          </div>
        )}

        {phase === 'triage' && (
          <div className="space-y-12 animate-in fade-in zoom-in-95 duration-500">
            {triageResultText && (
              <div className="max-w-4xl mx-auto p-6 bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl shadow-lg mb-8 text-lg leading-relaxed">
                <ReactMarkdown
                  components={{
                    p: ({node, ...props}) => <p className="mb-4 last:mb-0" {...props} />,
                    strong: ({node, ...props}) => <strong className="font-semibold text-violet-700 dark:text-violet-400" {...props} />
                  }}
                >
                  {triageResultText}
                </ReactMarkdown>
              </div>
            )}
            
            {triageRejected ? (
               <div className="flex justify-center mt-8 pt-8 border-t border-[var(--border-color)]">
                  <button 
                    onClick={() => {
                      setPhase('input');
                      setTriageResultText('');
                      setTriageRejected(false);
                      setSessionId(Math.random().toString(36).substring(7));
                    }}
                    className="px-12 py-4 bg-violet-600 hover:bg-violet-700 text-white font-bold rounded-2xl shadow-xl transition-all"
                  >
                    Try Again
                  </button>
               </div>
            ) : (
               <>
                 <div className="text-center space-y-4 max-w-3xl mx-auto">
                   <h2 className="text-4xl font-extrabold tracking-tight">Select an Epistemic Lens</h2>
                   <p className="text-lg opacity-70">Choose the academic framework that will drive the dialectical debate.</p>
                 </div>
     
                 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                   {LENSES.map((lens, idx) => (
                     <div 
                       key={lens.id}
                       onClick={() => startDebate(idx)}
                       className={`relative p-6 rounded-3xl border-2 cursor-pointer transition-all duration-300 overflow-hidden ${
                         selectedLensIndex === idx 
                           ? 'border-violet-500 bg-violet-500/5 shadow-xl shadow-violet-500/10' 
                           : 'border-[var(--border-color)] bg-[var(--card-bg)] hover:border-violet-500/50 hover:shadow-lg'
                       }`}
                     >
                       {selectedLensIndex === idx && <div className="absolute top-0 left-0 w-full h-1 bg-violet-500"></div>}
                       <div className="text-4xl mb-4">{lens.icon}</div>
                       <h3 className="text-xl font-bold mb-2">{lens.name}</h3>
                       <p className="opacity-70 text-sm leading-relaxed">{lens.description}</p>
                     </div>
                   ))}
                 </div>
     
                 {/* Single-selection mode: Debate starts immediately on card click.
                     Keep this button commented out for future multi-select features.
                 <div className="flex justify-center mt-12 pt-8 border-t border-[var(--border-color)]">
                   <button 
                     onClick={() => startDebate()}
                     disabled={selectedLensIndex === null}
                     className="px-12 py-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-2xl shadow-xl shadow-indigo-600/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 active:scale-95 text-lg"
                   >
                     Start Debate
                   </button>
                 </div>
                 */}
               </>
            )}
          </div>
        )}

        {phase === 'debate' && (
          <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in pt-8">
            <div className="text-center space-y-4">
              <div className="relative inline-block">
                {isTyping ? (
                  <div className="w-12 h-12 border-4 border-violet-500/30 border-t-violet-500 rounded-full animate-spin mx-auto"></div>
                ) : (
                  <div className="w-12 h-12 border-4 border-green-500/30 bg-green-500/10 text-green-500 rounded-full flex items-center justify-center mx-auto text-2xl font-bold">✓</div>
                )}
              </div>
              <h2 className="text-3xl font-extrabold">
                {isTyping ? "Live Debate" : "Synthesis Complete"}
              </h2>
              {isTyping && (
                <p className="text-md font-semibold text-violet-600 dark:text-violet-400 animate-pulse mt-2">
                  A little patience, please. Gemini’s gears are turning for you...
                </p>
              )}
              {selectedLensIndex !== null && (
                <div className="flex flex-col items-center gap-3">
                  <div className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-violet-100 to-indigo-100 dark:from-violet-900/40 dark:to-indigo-900/40 border border-violet-200 dark:border-violet-800/50 text-violet-900 dark:text-violet-100 rounded-full font-extrabold text-xl shadow-lg transform hover:scale-105 transition-transform duration-300">
                    <span className="text-3xl drop-shadow-sm">{LENSES[selectedLensIndex]?.icon}</span>
                    <span>Active Lens: {LENSES[selectedLensIndex]?.name}</span>
                  </div>
                  {targetAudience && (
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-[var(--card-bg)] border border-[var(--border-color)] opacity-80 rounded-full text-sm font-semibold shadow-sm transition-opacity hover:opacity-100">
                      <span className="text-lg">🎯</span>
                      <span>Target Audience: {targetAudience}</span>
                    </div>
                  )}
                  {thesis && (
                    <div className="mt-4 w-full max-w-3xl text-left bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl p-5 shadow-sm">
                      <div className="text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 font-bold mb-2 flex items-center gap-2">
                        <span>📝</span> Original Thesis
                      </div>
                      <div className="text-lg font-medium italic opacity-90">
                        "{thesis}"
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-3xl p-6 shadow-xl space-y-6 flex flex-col gap-6">
              {messages.map((msg, i) => {
                const isCitationChecker = msg.author.startsWith('citation_checker');
                const authorName = isCitationChecker ? 'Citation Checker' : msg.author.toUpperCase();
                
                if (isCitationChecker) {
                  if (msg.is_citation_error) return null;

                  return (
                    <div key={i} className="flex justify-center w-full my-2">
                      <div className="inline-flex items-start flex-col gap-2 px-4 py-3 bg-gray-100 dark:bg-gray-800 rounded-xl text-sm font-medium opacity-80 max-w-2xl">
                        <div className="flex items-center gap-2">
                          <span className="opacity-70 text-xs uppercase tracking-wider">{authorName}:</span>
                          {msg.content === "No citations to check." ? (
                            <span className="text-gray-500 dark:text-gray-400">No citations to check.</span>
                          ) : msg.content === "Citations verified." ? (
                            <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-1">✓ Citations verified.</span>
                          ) : null}
                        </div>
                          {msg.content !== "No citations to check." && msg.content !== "Citations verified." && (
                            <span className="text-emerald-600 dark:text-emerald-400 whitespace-pre-wrap leading-relaxed">{msg.content.replace("Citations verified.\n\n", "✓ Citations verified.\n\n")}</span>
                          )}
                        </div>
                    </div>
                  );
                }

                return (
                  <div key={i} className={`flex gap-4 w-[90%] ${msg.author === 'antagonist' ? 'self-end flex-row-reverse' : ''}`}>
                    <div className={`w-10 h-10 shrink-0 rounded-full flex items-center justify-center text-xl shadow-sm border ${msg.author === 'antagonist' ? 'bg-rose-100 border-rose-200 text-rose-600 dark:bg-rose-900/30 dark:border-rose-800' : 'bg-violet-100 border-violet-200 text-violet-600 dark:bg-violet-900/30 dark:border-violet-800'}`}>
                      {msg.author === 'antagonist' ? '🤺' : (LENSES[selectedLensIndex]?.icon || '🏛️')}
                    </div>
                    <div className={`space-y-2 flex flex-col ${msg.author === 'antagonist' ? 'items-end' : 'items-start'}`}>
                      <div className={`font-bold text-sm opacity-80 flex items-center gap-2 ${msg.author === 'antagonist' ? 'flex-row-reverse' : ''}`}>
                        {authorName}
                      </div>
                      <div className={`p-5 rounded-2xl text-base leading-relaxed ${
                        msg.author === 'antagonist' 
                          ? 'rounded-tr-none bg-rose-50 border border-rose-100 dark:bg-rose-900/10 dark:border-rose-900/30' 
                          : msg.author === 'synthesizer'
                          ? 'rounded-tl-none bg-violet-50 border border-violet-200 dark:bg-violet-900/20 dark:border-violet-800/40 shadow-inner shadow-violet-500/5'
                          : 'rounded-tl-none bg-gray-100 dark:bg-gray-800/50 border border-transparent'
                      }`}>
                        <ReactMarkdown
                          components={{
                            h1: ({node, ...props}) => <h1 className="text-2xl font-bold mt-5 mb-3" {...props} />,
                            h2: ({node, ...props}) => <h2 className="text-xl font-bold mt-5 mb-3" {...props} />,
                            h3: ({node, ...props}) => <h3 className="text-lg font-bold mt-4 mb-2" {...props} />,
                            p: ({node, ...props}) => <p className="mb-4 last:mb-0" {...props} />,
                            ul: ({node, ...props}) => <ul className="list-disc pl-6 mb-4 space-y-2" {...props} />,
                            ol: ({node, ...props}) => <ol className="list-decimal pl-6 mb-4 space-y-2" {...props} />,
                            li: ({node, ...props}) => <li className="pl-1" {...props} />,
                            strong: ({node, ...props}) => <strong className="font-semibold text-violet-700 dark:text-violet-400" {...props} />,
                            em: ({node, ...props}) => <em className="italic opacity-90" {...props} />,
                            blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-violet-500/50 pl-4 italic my-4 opacity-80" {...props} />,
                            a: ({node, children, ...props}) => (
                              <a 
                                className="inline-flex items-center gap-1 px-2 py-0.5 mx-1 bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/30 dark:hover:bg-blue-800/40 text-blue-700 dark:text-blue-300 rounded border border-blue-200 dark:border-blue-700/50 text-sm font-medium transition-colors no-underline" 
                                target="_blank" 
                                rel="noopener noreferrer" 
                                {...props}
                              >
                                <span className="opacity-70 text-xs">🔗</span>
                                <span>{children}</span>
                              </a>
                            )
                          }}
                        >
                          {(() => {
                            let txt = msg.content;
                            if (msg.author === 'judge') {
                              try {
                                const parsed = JSON.parse(msg.content);
                                let output = parsed.reasoning || '';
                                if (parsed.audience_feedback) {
                                  output += `\n\n**Audience Check:** ${parsed.audience_feedback}`;
                                }
                                txt = output;
                              } catch (e) {
                                txt = msg.content.replace(/\[DECISION: (CONTINUE|END)\]\s*/gi, '');
                              }
                            }
                            // Strip raw LaTeX math mode $...$ formatting if it leaked through
                            txt = txt.replace(/\$([^\$]+)\$/g, '$1');
                            // Strip hallucinated Gemini Search Grounding artifacts (e.g., "3]. 3]. 3].")
                            txt = txt.replace(/\s*\[?\d+\]\./g, '');
                            return txt;
                          })()}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                );
              })}

              {isTyping && (
                <div className="flex gap-4 w-[85%] opacity-70">
                  <div className="w-10 h-10 shrink-0 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 text-xl border border-gray-200 dark:bg-gray-800 dark:border-gray-700">
                    ⏳
                  </div>
                  <div className="space-y-2">
                    <div className="font-bold text-sm text-violet-600 dark:text-violet-400 mb-1">{currentActivity}</div>
                    <div className="p-4 rounded-2xl rounded-tl-none bg-gray-100 dark:bg-gray-800 flex gap-1.5 items-center w-16 h-12">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              )}

              {errorMessage && (
                <div className="mt-8 p-6 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-800 rounded-2xl text-red-700 dark:text-red-400 font-bold shadow-lg flex justify-between items-center">
                  <div>🚨 Backend Error: {errorMessage}</div>
                  {phase === 'debate' && !errorMessage.includes('Automatically reconnecting') && (
                    <button 
                      onClick={() => startDebate(selectedLensIndex, true)} 
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition whitespace-nowrap ml-4 shadow"
                    >
                      Resume Connection
                    </button>
                  )}
                </div>
              )}

              {!isTyping && !errorMessage && (
                <div className="flex justify-center mt-8 pt-8 border-t border-[var(--border-color)]">
                  <button 
                    onClick={() => {
                      setPhase('input');
                      setThesis('');
                      setSelectedLensIndex(null);
                      setMessages([]);
                      setSessionId(Math.random().toString(36).substring(7));
                    }}
                    className="px-8 py-4 bg-violet-600 hover:bg-violet-700 text-white font-bold rounded-2xl shadow-xl shadow-violet-600/30 transition-all transform hover:-translate-y-1 active:translate-y-0 text-lg flex items-center gap-2"
                  >
                    New Socratic Duel <span>↺</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
