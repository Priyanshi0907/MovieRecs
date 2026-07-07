import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Info, Star, ChevronLeft, ChevronRight } from 'lucide-react';
import { getBackdropUrl, getFallbackBackdrop } from '../api';

export default function HeroBanner({ movies }) {
  const navigate = useNavigate();
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (!movies || movies.length === 0) return;
    
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % movies.length);
    }, 8500); // Shift every 8.5 seconds for elegant scrolling

    return () => clearInterval(interval);
  }, [movies]);

  if (!movies || movies.length === 0) {
    return <div className="h-[60vh] bg-brand-bg w-full animate-pulse"></div>;
  }

  const activeMovie = movies[activeIndex];

  const handleNext = () => {
    setActiveIndex((prev) => (prev + 1) % movies.length);
  };

  const handlePrev = () => {
    setActiveIndex((prev) => (prev - 1 + movies.length) % movies.length);
  };

  return (
    <div className="relative w-full h-[70vh] sm:h-[85vh] md:h-[95vh] bg-brand-bg overflow-hidden select-none">
      {/* Background Backdrop Image */}
      <div className="absolute inset-0 w-full h-full scale-100 transition-transform duration-[1500ms] ease-out">
        <img
          src={getBackdropUrl(activeMovie.backdrop_path)}
          alt={activeMovie.title}
          onError={(e) => {
            e.target.onerror = null;
            e.target.src = getFallbackBackdrop(activeMovie.id);
          }}
          className="w-full h-full object-cover opacity-45"
        />
        {/* Layer Gradients */}
        <div className="absolute inset-0 bg-gradient-to-r from-brand-bg via-brand-bg/60 to-transparent"></div>
        <div className="absolute inset-0 bg-gradient-to-t from-brand-bg via-transparent to-brand-bg/30"></div>
      </div>

      {/* Cinematic Content overlay */}
      <div className="absolute bottom-20 sm:bottom-28 left-6 md:left-16 max-w-xl sm:max-w-2xl px-4 z-30 space-y-5 animate-fade-in">
        {/* Genre Tags & Rating */}
        <div className="flex items-center space-x-3 text-xs font-semibold uppercase tracking-wider text-brand-secText">
          <span className="bg-brand-gold text-black px-2.5 py-0.5 rounded font-black tracking-wider text-[10px]">
            Featured Selection
          </span>
          <span>
            {activeMovie.release_date?.split('-')[0]}
          </span>
          <span>&bull;</span>
          <div className="flex items-center text-brand-gold font-extrabold">
            <Star className="w-3.5 h-3.5 fill-current mr-1" />
            {activeMovie.vote_average?.toFixed(1)}
          </div>
        </div>

        {/* Title */}
        <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-brand-text leading-none uppercase font-serif drop-shadow-2xl">
          {activeMovie.title}
        </h1>

        {/* Synopsis Hook */}
        <p className="text-sm sm:text-base text-brand-secText line-clamp-3 leading-relaxed max-w-xl">
          {activeMovie.overview}
        </p>

        {/* Call to Actions */}
        <div className="flex items-center space-x-4 pt-3">
          <button 
            onClick={() => navigate(`/movie/${activeMovie.id}`)}
            className="flex items-center space-x-2 bg-brand-gold hover:bg-brand-lightgold text-black font-black px-7 py-3 rounded-lg transition duration-300 shadow-xl text-xs uppercase tracking-widest glow-gold"
          >
            <Play className="w-4 h-4 fill-black" />
            <span>Play Trailer</span>
          </button>
          
          <button 
            onClick={() => navigate(`/movie/${activeMovie.id}`)}
            className="flex items-center space-x-2 bg-brand-card/85 hover:bg-brand-card text-brand-text border border-white/5 font-bold px-7 py-3 rounded-lg transition duration-300 shadow-md text-xs uppercase tracking-widest glass-light"
          >
            <Info className="w-4 h-4 text-brand-gold" />
            <span>More Info</span>
          </button>
        </div>
      </div>

      {/* Manual Slideshow Controls */}
      <button 
        onClick={handlePrev}
        className="absolute left-6 top-1/2 -translate-y-1/2 p-2.5 rounded-full bg-black/40 hover:bg-brand-gold hover:text-black transition duration-300 text-brand-secText z-30 hidden sm:block focus:outline-none border border-white/5"
      >
        <ChevronLeft className="w-5 h-5" />
      </button>
      <button 
        onClick={handleNext}
        className="absolute right-6 top-1/2 -translate-y-1/2 p-2.5 rounded-full bg-black/40 hover:bg-brand-gold hover:text-black transition duration-300 text-brand-secText z-30 hidden sm:block focus:outline-none border border-white/5"
      >
        <ChevronRight className="w-5 h-5" />
      </button>

      {/* Slide Indicators */}
      <div className="absolute bottom-10 right-16 flex space-x-2.5 z-30">
        {movies.slice(0, 5).map((_, idx) => (
          <button
            key={idx}
            onClick={() => setActiveIndex(idx)}
            className={`h-1.5 rounded-full transition-all duration-300 ${idx === activeIndex ? 'w-8 bg-brand-gold glow-gold' : 'w-2 bg-brand-secText/40'}`}
          ></button>
        ))}
      </div>
    </div>
  );
}
