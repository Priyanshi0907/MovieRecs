import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock, User, ArrowRight, LogIn } from 'lucide-react';
import { api } from '../api';

export default function Login() {
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let data;
      if (isRegister) {
        data = await api.post('/auth/register', { name, email, password });
      } else {
        data = await api.post('/auth/login', { email, password });
      }

      localStorage.setItem("token", data.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || "Authentication failed. Check your connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleGuestContinue = () => {
    localStorage.removeItem("token");
    navigate('/dashboard');
  };

  return (
    <div className="relative min-h-screen bg-brand-bg flex items-center justify-center p-4 overflow-hidden">
      {/* Background Poster Overlay */}
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-10 pointer-events-none"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070&auto=format&fit=crop')`
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent to-brand-bg z-10" />

      {/* Brand logo top left */}
      <div className="absolute top-8 left-8 z-20">
        <h1 
          onClick={() => navigate('/')}
          className="text-brand-gold text-2xl font-black tracking-tight font-serif cursor-pointer"
        >
          MovieRecs
        </h1>
      </div>

      {/* Login Card */}
      <div className="relative z-20 w-full max-w-sm bg-brand-secondary/80 border border-white/10 rounded-2xl shadow-2xl p-8 sm:p-10 flex flex-col space-y-6 glass">
        <div className="text-center space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold text-brand-text uppercase tracking-tight font-serif">
            {isRegister ? 'Register' : 'Sign In'}
          </h2>
          <p className="text-xs text-brand-secText">
            {isRegister ? 'Sign up to build your custom movie profile' : 'Enter details to access your cinematic selections'}
          </p>
        </div>

        {error && (
          <div className="bg-brand-gold/10 border border-brand-gold/30 rounded-lg p-3 text-xs text-brand-gold font-bold text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div className="space-y-1.5">
              <label className="text-[10px] uppercase font-bold text-brand-secText tracking-wider">Full Name</label>
              <div className="flex items-center bg-black/40 border border-white/5 rounded-lg px-3 py-2.5 focus-within:border-brand-gold transition duration-200">
                <User className="text-brand-secText w-4 h-4 mr-2" />
                <input
                  type="text"
                  placeholder="Jane Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="bg-transparent border-none text-xs w-full focus:outline-none text-brand-text placeholder-brand-secText/40"
                />
              </div>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-[10px] uppercase font-bold text-brand-secText tracking-wider">Email Address</label>
            <div className="flex items-center bg-black/40 border border-white/5 rounded-lg px-3 py-2.5 focus-within:border-brand-gold transition duration-200">
              <Mail className="text-brand-secText w-4 h-4 mr-2" />
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-transparent border-none text-xs w-full focus:outline-none text-brand-text placeholder-brand-secText/40"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] uppercase font-bold text-brand-secText tracking-wider">Password</label>
            <div className="flex items-center bg-black/40 border border-white/5 rounded-lg px-3 py-2.5 focus-within:border-brand-gold transition duration-200">
              <Lock className="text-brand-secText w-4 h-4 mr-2" />
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-transparent border-none text-xs w-full focus:outline-none text-brand-text placeholder-brand-secText/40"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center space-x-2 bg-brand-gold hover:bg-brand-lightgold text-black text-xs font-black py-3.5 rounded-lg shadow-lg transition duration-300 uppercase tracking-widest disabled:opacity-50 glow-gold"
          >
            {loading ? (
              <span>Authenticating...</span>
            ) : (
              <>
                <LogIn className="w-3.5 h-3.5" />
                <span>{isRegister ? 'Register' : 'Sign In'}</span>
              </>
            )}
          </button>
        </form>

        <div className="relative flex py-1 items-center">
          <div className="flex-grow border-t border-white/5"></div>
          <span className="flex-shrink mx-4 text-[9px] font-extrabold uppercase text-brand-secText tracking-wider">Or explore with</span>
          <div className="flex-grow border-t border-white/5"></div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => alert("Google Sign-In is coming soon!")}
            type="button"
            className="flex items-center justify-center space-x-2 bg-white/5 hover:bg-white/10 text-brand-text border border-white/5 rounded-lg py-2.5 text-xs font-semibold transition duration-200 glass-light"
          >
            <svg className="w-3.5 h-3.5 mr-1" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335"/>
            </svg>
            <span>Google</span>
          </button>
          
          <button
            onClick={handleGuestContinue}
            type="button"
            className="flex items-center justify-center space-x-1.5 bg-white/5 hover:bg-white/10 text-brand-text border border-white/5 rounded-lg py-2.5 text-xs font-semibold transition duration-200 glass-light"
          >
            <ArrowRight className="w-3.5 h-3.5 text-brand-gold" />
            <span>Guest Mode</span>
          </button>
        </div>

        <div className="text-center text-xs">
          <button
            type="button"
            onClick={() => setIsRegister(!isRegister)}
            className="text-brand-secText hover:text-brand-gold transition duration-200"
          >
            {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Register"}
          </button>
        </div>
      </div>
    </div>
  );
}
