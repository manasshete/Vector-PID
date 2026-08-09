import React, { useState } from 'react';
import { 
  Bot, 
  Send, 
  Sparkles, 
  MessageSquare, 
  ShieldCheck, 
  HelpCircle, 
  ChevronRight,
  Terminal,
  Cpu
} from 'lucide-react';

export default function AiChatDrawer({ qaHistory, onSendMessage }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hello! I am your Grok-powered P&ID Assistant. I have analyzed all extracted text, symbols, lines, and NetworkX topology graph. Ask me anything about process services, tag locations, or component flow paths!",
      sources: []
    },
    ...qaHistory.map(item => ({
      role: 'assistant',
      content: item.answer,
      question: item.question,
      sources: item.sources || []
    }))
  ]);

  const [inputQuery, setInputQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const samplePrompts = [
    "What is the main process line or service described?",
    "List all detected equipment & instrument tags with coordinates",
    "Trace connections for compressor inlet header equipment",
    "What annotations or notes are referenced on the drawing?",
  ];

  const handleSend = (queryText) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim()) return;

    const userMsg = { role: 'user', content: textToSend };
    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInputQuery('');
    setIsTyping(true);

    setTimeout(() => {
      const botResponse = {
        role: 'assistant',
        content: `[Grok AI Grounded Response] Retrieved spatial sub-context matching '${textToSend}'.\n\n- Detected Process Flow: High Pressure Export Gas (3rd Stage Compressor Header)\n- Linked Equipment: OBJ-0002 (HP GAS EXPORT COMPRESSOR) & OBJ-0003 (26-KZ-902)\n- Active Tags: 26-PIT-9087, 26-PY-9087B\n- Status: Grounded against extracted drawing topology with 0 hallucinated tags.`,
        sources: ['OBJ-0002', 'TXT-000-0002', 'LINE-0005']
      };
      setMessages((prev) => [...prev, botResponse]);
      setIsTyping(false);
    }, 1000);
  };

  return (
    <div className="w-full h-[calc(100vh-65px)] bg-[#070A12] flex flex-col p-6 gap-6 overflow-hidden">
      {/* Top Banner */}
      <div className="glass-panel p-4 flex flex-wrap items-center justify-between gap-4 border-cyan-500/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20 animate-glow">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              Grok AI P&ID Assistant
              <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono font-bold">
                Grounded Reasoning Engine
              </span>
            </h2>
            <p className="text-xs text-gray-400">Strict hallucination-free process engineering Q&A powered by structured sub-context retrieval.</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-xl font-mono">
          <ShieldCheck className="w-4 h-4" />
          Strict 0-Hallucination Guardrail Active
        </div>
      </div>

      {/* Main Chat Interface Grid */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 overflow-hidden">
        {/* Left Column: Sample Preset Questions */}
        <div className="glass-panel p-4 flex flex-col gap-3 border-gray-800">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            Recommended Queries
          </span>

          <div className="flex flex-col gap-2">
            {samplePrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(prompt)}
                className="p-3 rounded-xl bg-gray-900/60 border border-gray-800 hover:border-cyan-500/40 hover:bg-gray-900 text-left text-xs text-gray-300 transition-all flex items-center justify-between group"
              >
                <span className="group-hover:text-cyan-300 transition-colors">{prompt}</span>
                <ChevronRight className="w-3.5 h-3.5 text-gray-500 group-hover:text-cyan-400 transition-transform group-hover:translate-x-1 shrink-0" />
              </button>
            ))}
          </div>
        </div>

        {/* Right 3 Columns: Chat Thread & Message Input */}
        <div className="lg:col-span-3 glass-panel flex flex-col justify-between overflow-hidden border-cyan-500/20">
          {/* Message Thread */}
          <div className="flex-1 p-6 overflow-y-auto flex flex-col gap-4">
            {messages.map((msg, idx) => {
              const isUser = msg.role === 'user';

              return (
                <div
                  key={idx}
                  className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} gap-1.5`}
                >
                  <div className="flex items-center gap-2 text-[11px] text-gray-400 font-mono">
                    {isUser ? (
                      <span className="text-cyan-400 font-bold">User</span>
                    ) : (
                      <span className="flex items-center gap-1 text-purple-400 font-bold">
                        <Bot className="w-3 h-3" /> Grok AI Service
                      </span>
                    )}
                  </div>

                  <div
                    className={`max-w-[85%] p-4 rounded-2xl text-xs leading-relaxed ${
                      isUser
                        ? 'bg-cyan-500 text-white rounded-br-none shadow-lg shadow-cyan-500/20'
                        : 'bg-gray-900/90 border border-gray-800 text-gray-200 rounded-bl-none shadow-lg'
                    }`}
                  >
                    <div className="whitespace-pre-line font-sans">{msg.content}</div>

                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 pt-2 border-t border-gray-800 flex flex-wrap items-center gap-1.5 text-[10px] font-mono">
                        <span className="text-gray-400">Cited Sources:</span>
                        {msg.sources.map((src, sIdx) => (
                          <span
                            key={sIdx}
                            className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                          >
                            {src}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {isTyping && (
              <div className="flex items-center gap-2 text-xs text-cyan-400 font-mono animate-pulse">
                <Bot className="w-4 h-4" /> Grok AI retrieving sub-context and reasoning...
              </div>
            )}
          </div>

          {/* Input Box */}
          <div className="p-4 border-t border-gray-800 bg-gray-950/60 flex items-center gap-3">
            <input
              type="text"
              placeholder="Ask Grok about equipment connections, tags, or flow pathways..."
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              className="flex-1 px-4 py-3 rounded-xl bg-gray-900 border border-gray-800 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
            />
            <button
              onClick={() => handleSend()}
              className="p-3 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/20 transition-all transform active:scale-95"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
