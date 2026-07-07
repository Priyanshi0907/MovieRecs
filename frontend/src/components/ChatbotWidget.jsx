import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageSquare, X, Send, Film, Star, Sparkles } from 'lucide-react';
import { api, getPosterUrl, getFallbackPoster } from '../api';

export default function ChatbotWidget() {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: "Hey! I'm your AI Movie Companion. Ask me for recommendations! For example: *'I want a space movie like Interstellar'*, or *'Show me dark psychological thrillers directed by Scorsese'*.",
      movies: []
    }
  ]);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userText = query;
    setQuery('');
    setMessages(prev => [...prev, { sender: 'user', text: userText, movies: [] }]);
    setLoading(true);

    try {
      const res = await api.post('/chatbot', { query: userText });
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: res.message,
        movies: res.movies || []
      }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: "I ran into a connection issue with the recommendation brain. Please make sure the backend is active!",
        movies: []
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleMovieClick = (id) => {
    setIsOpen(false);
    navigate(`/movie/${id}`);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 select-none">
      {/* Floating Button Bubble */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center justify-center w-14 h-14 rounded-full bg-brand-gold text-black hover:bg-brand-lightgold transition-all duration-300 shadow-2xl focus:outline-none hover:scale-110 active:scale-95 group relative border border-white/10 glow-gold"
        >
          <MessageSquare className="w-6 h-6 group-hover:rotate-12 transition-transform duration-300" />
          <span className="absolute -top-1 -right-1 bg-brand-text text-black text-[8px] font-black rounded-full px-1.5 py-0.5 uppercase tracking-wide flex items-center space-x-0.5">
            <Sparkles className="w-2.5 h-2.5 fill-current" />
            <span>AI</span>
          </span>
        </button>
      )}

      {/* Expanded Chat Drawer */}
      {isOpen && (
        <div className="w-80 sm:w-96 h-[450px] sm:h-[500px] bg-brand-secondary border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-slide-up glass animate-fade-in">
          {/* Chat Header */}
          <div className="bg-white/5 px-4 py-3.5 border-b border-white/5 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="relative">
                <div className="w-8 h-8 rounded-full bg-brand-gold flex items-center justify-center">
                  <Film className="w-4 h-4 text-black" />
                </div>
                <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-green-500 border border-brand-secondary"></span>
              </div>
              <div>
                <h3 className="text-xs font-black text-brand-text uppercase tracking-wider font-serif">
                  Movie AI Companion
                </h3>
                <span className="text-[9px] text-brand-secText font-medium">Powered by Gemini</span>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-brand-secText hover:text-white transition-colors duration-200 focus:outline-none"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages Logs Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 no-scrollbar">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-xs leading-relaxed ${
                    msg.sender === 'user'
                      ? 'bg-brand-gold text-black font-semibold rounded-br-none shadow-md'
                      : 'bg-white/5 border border-white/5 text-brand-text rounded-bl-none'
                  }`}
                >
                  {msg.text}
                </div>

                {/* Render Inline Suggested Movie Cards */}
                {msg.movies && msg.movies.length > 0 && (
                  <div className="mt-2.5 w-full space-y-2 pl-3 border-l border-brand-gold/30">
                    <div className="text-[9px] font-bold text-brand-secText uppercase tracking-wider mb-1">
                      Matched Recommendations:
                    </div>
                    {msg.movies.map((m) => (
                      <div
                        key={m.id}
                        onClick={() => handleMovieClick(m.id)}
                        className="flex items-center space-x-2.5 p-2 rounded-xl bg-black/40 hover:bg-white/5 border border-white/5 cursor-pointer transition-colors duration-250"
                      >
                        <img
                          src={getPosterUrl(m.poster_path, 'w92', m.id)}
                          alt={m.title}
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = getFallbackPoster(m.id);
                          }}
                          className="w-7 h-10 object-cover rounded border border-white/5"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-[11px] font-bold truncate text-brand-text font-serif">{m.title}</p>
                          <p className="text-[9px] text-brand-secText truncate">{m.genres?.slice(0, 2).join(', ')}</p>
                        </div>
                        <div className="flex items-center text-[10px] text-brand-gold font-extrabold pr-1">
                          <Star className="w-2.5 h-2.5 fill-current mr-0.5" />
                          {m.vote_average?.toFixed(1)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            
            {/* Thinking Indicator */}
            {loading && (
              <div className="flex items-center space-x-1.5 bg-white/5 border border-white/5 rounded-2xl rounded-bl-none px-3.5 py-2.5 max-w-[50%] animate-pulse">
                <span className="w-1.5 h-1.5 rounded-full bg-brand-gold animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-1.5 h-1.5 rounded-full bg-brand-gold animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-1.5 h-1.5 rounded-full bg-brand-gold animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            )}
            
            <div ref={chatEndRef} />
          </div>

          {/* Message Input Panel */}
          <form onSubmit={handleSend} className="p-3 bg-white/5 border-t border-white/5 flex items-center space-x-2">
            <input
              type="text"
              placeholder="Ask for recommendations..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
              className="flex-1 bg-black/60 border border-white/10 rounded-full px-4 py-2 text-xs focus:outline-none focus:border-brand-gold text-brand-text placeholder-brand-secText/50 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!query.trim() || loading}
              className="p-2 rounded-full bg-brand-gold hover:bg-brand-lightgold text-black transition-colors duration-200 focus:outline-none disabled:opacity-40 disabled:hover:bg-brand-gold"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
