import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Sparkles, LogIn, Compass } from 'lucide-react';

export default function LandingPage() {
  const navigate = useNavigate();

  const handleGuestContinue = () => {
    localStorage.removeItem("token");
    navigate('/dashboard');
  };

  return (
    <div className="relative min-h-screen bg-brand-bg flex flex-col justify-between overflow-hidden">
      {/* Cinematic Background Poster Grid */}
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-15 scale-105 pointer-events-none"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=1925&auto=format&fit=crop')`
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-brand-bg via-brand-bg/85 to-brand-bg z-10" />

      {/* Header */}
      <header className="relative z-20 px-6 md:px-16 py-6 flex items-center justify-between border-b border-white/5 bg-brand-bg/30 backdrop-blur-sm">
        <h1 className="text-brand-gold text-2xl font-black tracking-tight font-serif hover:scale-105 transition-transform duration-300 cursor-pointer">
          MovieRecs
        </h1>
        
        <button
          onClick={() => navigate('/login')}
          className="flex items-center space-x-1.5 bg-brand-gold hover:bg-brand-lightgold text-black text-xs font-black px-5 py-2.5 rounded-md shadow-lg transition duration-300 uppercase tracking-wider"
        >
          <LogIn className="w-3.5 h-3.5" />
          <span>Login / Register</span>
        </button>
      </header>

      {/* Main Hero Section */}
      <main className="relative z-20 flex-1 max-w-5xl mx-auto flex flex-col items-center justify-center text-center px-6 py-16 md:py-28 space-y-8">
        <div className="inline-flex items-center space-x-2 bg-brand-card/65 border border-white/10 rounded-full px-4 py-1.5 text-xs text-brand-gold font-bold uppercase tracking-wider glass">
          <Sparkles className="w-4 h-4 fill-current animate-pulse" />
          <span>Hybrid AI Recommender Engine</span>
        </div>

        <h2 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-brand-text leading-none font-serif">
          UNLIMITED CINEMA.<br />
          <span className="bg-gradient-to-r from-brand-gold via-[#F3CD57] to-white bg-clip-text text-transparent italic">
            CURATED FOR YOU.
          </span>
        </h2>

        <p className="text-sm sm:text-base text-brand-secText max-w-2xl leading-relaxed">
          Stop scrolling endlessly. MovieRecs learns from your preferences, ratings, and viewing moods using custom SVD matrix factorizations and content metadata tags to construct film lists you will actually love.
        </p>

        {/* Action CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4 w-full max-w-md">
          <button
            onClick={() => navigate('/login')}
            className="w-full sm:w-auto flex items-center justify-center space-x-2 bg-brand-gold hover:bg-brand-lightgold text-black font-black px-8 py-3.5 rounded-lg shadow-2xl transition duration-300 text-xs uppercase tracking-wider glow-gold"
          >
            <Play className="w-3.5 h-3.5 fill-black" />
            <span>Sign In to Start</span>
          </button>
          
          <button
            onClick={handleGuestContinue}
            className="w-full sm:w-auto flex items-center justify-center space-x-2 bg-white/5 hover:bg-white/10 text-brand-text font-black px-8 py-3.5 rounded-lg border border-white/10 transition duration-300 text-xs uppercase tracking-wider glass-light"
          >
            <Compass className="w-3.5 h-3.5 text-brand-gold" />
            <span>Explore as Guest</span>
          </button>
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-16 max-w-4xl text-left text-xs">
          <div className="bg-brand-card/40 border border-white/5 p-6 rounded-2xl space-y-2 glass">
            <h4 className="text-xs font-bold text-brand-text uppercase tracking-wider flex items-center space-x-2 font-serif">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-gold"></span>
              <span>SVD & Cosine Hybrid</span>
            </h4>
            <p className="text-brand-secText leading-relaxed">
              Blends structural content keywords (directors, genre mappings, actors) with matrices predicting ratings from like-minded users.
            </p>
          </div>
          <div className="bg-brand-card/40 border border-white/5 p-6 rounded-2xl space-y-2 glass">
            <h4 className="text-xs font-bold text-brand-text uppercase tracking-wider flex items-center space-x-2 font-serif">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-gold"></span>
              <span>Gemini AI Chatbot</span>
            </h4>
            <p className="text-brand-secText leading-relaxed">
              Ask questions directly like *"I want a mind-bending space thriller like Interstellar but darker"* and receive suggestion titles instantly.
            </p>
          </div>
          <div className="bg-brand-card/40 border border-white/5 p-6 rounded-2xl space-y-2 glass">
            <h4 className="text-xs font-bold text-brand-text uppercase tracking-wider flex items-center space-x-2 font-serif">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-gold"></span>
              <span>Taste Analytics</span>
            </h4>
            <p className="text-brand-secText leading-relaxed">
              Visualize your watch history distributions, favorite genres, and yearly watch graphs through glowing interactive charts.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-20 px-6 py-6 border-t border-white/5 bg-black/30 text-center text-[10px] uppercase font-bold tracking-widest text-brand-secText/50">
        &copy; 2026 MovieRecs. IMDb meets Apple meets A24.
      </footer>
    </div>
  );
}
