import React, { useState } from 'react';
import { Send, Sparkles, ChevronRight } from 'lucide-react';
import { askQuestion } from '../lib/api';

export default function AiChatDrawer({ apiOnline, hasAnalysis }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: hasAnalysis
        ? 'Connected to the Python Grok service. Ask about tags, equipment, or flow paths from the loaded analysis.'
        : apiOnline
          ? 'API is online. Upload a P&ID to run the pipeline, then ask grounded questions here.'
          : 'Start the API server (python scripts/run_api.py) and upload a drawing to enable live Q&A.',
      sources: [],
    },
  ]);

  const [inputQuery, setInputQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const samplePrompts = [
    'What is the main process line or service?',
    'List equipment and instrument tags',
    'Trace compressor inlet header connections',
    'What annotations appear on the drawing?',
  ];

  const handleSend = async (queryText) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || isTyping) return;

    setMessages((prev) => [...prev, { role: 'user', content: textToSend }]);
    if (!queryText) setInputQuery('');
    setIsTyping(true);

    try {
      if (!apiOnline || !hasAnalysis) {
        throw new Error('Upload a drawing via the API before asking questions.');
      }
      const { answer, sources } = await askQuestion(textToSend);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: answer, sources: sources || [] },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: err.message || 'Could not reach the Grok API.',
          sources: [],
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="w-full h-[calc(100vh-57px)] flex flex-col p-5 gap-4 overflow-hidden">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-[17px] font-semibold tracking-tight text-[var(--text)]">Ask AI</h2>
          <p className="text-[13px] text-[var(--text-muted)] mt-0.5">
            {hasAnalysis ? 'Grounded via Python Grok service' : 'Requires uploaded analysis'}
          </p>
        </div>
        <span
          className={`text-[11px] font-medium px-2.5 py-1 rounded-md ${
            hasAnalysis
              ? 'text-[var(--accent)] bg-[var(--accent-soft)]'
              : 'text-[var(--text-muted)] bg-[var(--bg-muted)]'
          }`}
        >
          {hasAnalysis ? 'Live' : 'Offline'}
        </span>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-4 overflow-hidden min-h-0">
        <div className="panel p-4 flex flex-col gap-3 overflow-y-auto">
          <span className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" strokeWidth={1.75} />
            Suggestions
          </span>

          <div className="flex flex-col gap-1.5">
            {samplePrompts.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleSend(prompt)}
                disabled={isTyping}
                className="p-3 rounded-lg border border-[var(--border)] hover:bg-[var(--bg-muted)] text-left text-[12px] text-[var(--text-secondary)] transition-colors flex items-start justify-between gap-2 group disabled:opacity-50"
              >
                <span className="group-hover:text-[var(--text)] leading-relaxed">{prompt}</span>
                <ChevronRight
                  className="w-3.5 h-3.5 text-[var(--text-muted)] shrink-0 mt-0.5 group-hover:translate-x-0.5 transition-transform"
                  strokeWidth={1.75}
                />
              </button>
            ))}
          </div>
        </div>

        <div className="lg:col-span-3 panel flex flex-col overflow-hidden min-h-0">
          <div className="flex-1 p-5 overflow-y-auto flex flex-col gap-4">
            {messages.map((msg, idx) => {
              const isUser = msg.role === 'user';

              return (
                <div key={idx} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} gap-1`}>
                  <span className="text-[11px] text-[var(--text-muted)] px-1">
                    {isUser ? 'You' : 'Assistant'}
                  </span>

                  <div
                    className={`max-w-[85%] px-4 py-3 rounded-2xl text-[13px] leading-relaxed ${
                      isUser
                        ? 'bg-[var(--ink)] text-white rounded-br-md'
                        : 'bg-[var(--bg-muted)] text-[var(--text)] rounded-bl-md'
                    }`}
                  >
                    <div className="whitespace-pre-line">{msg.content}</div>

                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 pt-2.5 border-t border-[var(--border)] flex flex-wrap items-center gap-1.5 text-[11px] font-[family-name:var(--font-mono)]">
                        <span className="text-[var(--text-muted)]">Sources</span>
                        {msg.sources.map((src) => (
                          <span
                            key={src}
                            className="px-1.5 py-0.5 rounded bg-[var(--bg-elevated)] text-[var(--text-secondary)] border border-[var(--border)]"
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
              <div className="flex items-center gap-1.5 text-[12px] text-[var(--text-muted)] px-1">
                <span className="typing-dot">●</span>
                <span className="typing-dot" style={{ animationDelay: '0.2s' }}>
                  ●
                </span>
                <span className="typing-dot" style={{ animationDelay: '0.4s' }}>
                  ●
                </span>
              </div>
            )}
          </div>

          <div className="p-3 border-t border-[var(--border)] flex items-center gap-2">
            <input
              type="text"
              placeholder="Ask about tags, connections, or flow…"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              disabled={isTyping}
              className="flex-1 px-3.5 py-2.5 rounded-lg bg-[var(--bg-muted)] border border-transparent text-[13px] text-[var(--text)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--border-strong)] focus:bg-[var(--bg-elevated)] transition-colors disabled:opacity-50"
            />
            <button
              onClick={() => handleSend()}
              disabled={isTyping}
              className="p-2.5 rounded-lg bg-[var(--ink)] hover:bg-[var(--text)] text-white transition-colors disabled:opacity-50"
              aria-label="Send"
            >
              <Send className="w-4 h-4" strokeWidth={1.75} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
