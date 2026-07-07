import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Film, User, Clock, Compass, ArrowRight, ArrowLeft, CheckCircle, Sparkles } from 'lucide-react';
import { api } from '../api';

export default function Questionnaire() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);

  const [genres, setGenres] = useState([]);
  const [actors, setActors] = useState([]);
  const [directors, setDirectors] = useState([]);
  const [languages, setLanguages] = useState(["English"]);
  const [runtime, setRuntime] = useState("90-120 mins");
  const [mood, setMood] = useState("Feel-good");

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const u = await api.get('/auth/me');
        if (u) {
          if (u.genres) setGenres(u.genres);
          if (u.actors) setActors(u.actors);
          if (u.directors) setDirectors(u.directors);
          if (u.languages) setLanguages(u.languages);
          if (u.runtime) setRuntime(u.runtime);
          if (u.mood) setMood(u.mood);
        }
      } catch (err) {
        console.error("Failed to load existing user questionnaire data", err);
      }
    };
    loadProfile();
  }, []);

  const genreOptions = ["Action", "Comedy", "Romance", "Crime", "Thriller", "Fantasy", "Sci-Fi", "Anime", "Drama", "Adventure", "Mystery"];
  const directorOptions = ["Christopher Nolan", "Quentin Tarantino", "David Fincher", "Martin Scorsese", "Damien Chazelle", "Bong Joon-ho", "Hayao Miyazaki", "Denis Villeneuve", "Ridley Scott", "Steven Spielberg", "James Cameron"];
  const actorOptions = ["Leonardo DiCaprio", "Brad Pitt", "Ryan Gosling", "Emma Stone", "Matthew McConaughey", "Anne Hathaway", "Jessica Chastain", "Christian Bale", "Scarlett Johansson", "Matt Damon", "Ana de Armas", "Song Kang-ho"];
  const langOptions = ["English", "Japanese", "Spanish", "French", "Korean", "German"];
  
  const moodOptions = [
    { label: "😊 Happy", val: "Happy" },
    { label: "😭 Emotional / Sad", val: "Sad" },
    { label: "🧠 Mind Bending", val: "Mind-bending" },
    { label: "😌 Feel-good", val: "Feel-good" },
    { label: "😱 Dark / Suspense", val: "Dark" },
    { label: "🍿 Family Time", val: "Family" }
  ];

  const toggleGenre = (g) => {
    setGenres(prev => prev.includes(g) ? prev.filter(x => x !== g) : [...prev, g]);
  };

  const toggleDirector = (d) => {
    setDirectors(prev => prev.includes(d) ? prev.filter(x => x !== d) : [...prev, d]);
  };

  const toggleActor = (a) => {
    setActors(prev => prev.includes(a) ? prev.filter(x => x !== a) : [...prev, a]);
  };

  const toggleLang = (l) => {
    setLanguages(prev => prev.includes(l) ? prev.filter(x => x !== l) : [...prev, l]);
  };

  const handleSubmit = async () => {
    try {
      await api.post('/user/questionnaire', {
        genres,
        languages,
        actors,
        directors,
        runtime,
        mood,
        age: 25,
        region: "United States"
      });
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
      alert("Failed to submit questionnaire. Proceeding to Dashboard anyway.");
      navigate('/dashboard');
    }
  };

  return (
    <div className="relative min-h-screen bg-brand-bg flex flex-col justify-center items-center p-4">
      {/* Background glow effects */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-gold/5 rounded-full blur-[120px] pointer-events-none"></div>

      {/* Progress indicators bar */}
      <div className="w-full max-w-2xl mb-8 flex items-center justify-between relative px-2">
        <div className="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 bg-white/5 w-full z-0"></div>
        <div 
          className="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 bg-brand-gold transition-all duration-300 z-0" 
          style={{ width: `${((step - 1) / 3) * 100}%` }}
        ></div>

        {[1, 2, 3, 4].map((num) => (
          <div
            key={num}
            className={`w-7 h-7 rounded-full flex items-center justify-center font-bold z-10 transition-all duration-300 border text-[10px] ${
              step >= num 
                ? 'bg-brand-gold text-black border-brand-gold glow-gold' 
                : 'bg-brand-secondary text-brand-secText border-white/5'
            }`}
          >
            {num}
          </div>
        ))}
      </div>

      {/* Main Questionnaire Box */}
      <div className="w-full max-w-2xl bg-brand-secondary/90 border border-white/10 rounded-2xl p-6 sm:p-10 shadow-2xl space-y-8 glass select-none">
        {step === 1 && (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-xl sm:text-2xl font-bold text-brand-text flex items-center font-serif uppercase tracking-tight">
                <Film className="w-5 h-5 text-brand-gold mr-2" />
                Select Favorite Genres
              </h2>
              <p className="text-xs text-brand-secText">Choose the genres you enjoy watching most. This forms the baseline of your profile.</p>
            </div>
            
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {genreOptions.map((g) => {
                const active = genres.includes(g);
                return (
                  <button
                    key={g}
                    onClick={() => toggleGenre(g)}
                    className={`py-3 px-4 rounded-xl border text-xs font-bold transition-all duration-300 flex items-center justify-between ${
                      active 
                        ? 'border-brand-gold bg-brand-gold/15 text-brand-text shadow-md' 
                        : 'border-white/5 bg-white/5 text-brand-secText hover:border-white/20 hover:text-white'
                    }`}
                  >
                    <span>{g}</span>
                    {active && <CheckCircle className="w-4 h-4 text-brand-gold fill-brand-gold/10" />}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-xl sm:text-2xl font-bold text-brand-text flex items-center font-serif uppercase tracking-tight">
                <User className="w-5 h-5 text-brand-gold mr-2" />
                Favorite Directors & Actors
              </h2>
              <p className="text-xs text-brand-secText">Select filmmakers or talent to personalize your recommendations.</p>
            </div>

            <div className="space-y-4">
              <h3 className="text-xs font-extrabold text-brand-secText uppercase tracking-wider">Directors</h3>
              <div className="flex flex-wrap gap-2">
                {directorOptions.map((d) => {
                  const active = directors.includes(d);
                  return (
                    <button
                      key={d}
                      onClick={() => toggleDirector(d)}
                      className={`py-2 px-3.5 rounded-full border text-xs font-semibold transition-all duration-200 ${
                        active 
                          ? 'border-brand-gold bg-brand-gold text-black font-bold' 
                          : 'border-white/5 bg-white/5 text-brand-secText hover:text-white hover:border-white/20'
                      }`}
                    >
                      {d}
                    </button>
                  );
                })}
              </div>

              <h3 className="text-xs font-extrabold text-brand-secText uppercase tracking-wider pt-2">Actors</h3>
              <div className="flex flex-wrap gap-2">
                {actorOptions.map((a) => {
                  const active = actors.includes(a);
                  return (
                    <button
                      key={a}
                      onClick={() => toggleActor(a)}
                      className={`py-2 px-3.5 rounded-full border text-xs font-semibold transition-all duration-200 ${
                        active 
                          ? 'border-brand-gold bg-brand-gold text-black font-bold' 
                          : 'border-white/5 bg-white/5 text-brand-secText hover:text-white hover:border-white/20'
                      }`}
                    >
                      {a}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-xl sm:text-2xl font-bold text-brand-text flex items-center font-serif uppercase tracking-tight">
                <Clock className="w-5 h-5 text-brand-gold mr-2" />
                Language & Runtime Length
              </h2>
              <p className="text-xs text-brand-secText">Specify languages and ideal movie runtimes for filtering recommendations.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Languages */}
              <div className="space-y-3">
                <h3 className="text-xs font-extrabold text-brand-secText uppercase tracking-wider">Preferred Languages</h3>
                <div className="flex flex-wrap gap-2">
                  {langOptions.map((l) => {
                    const active = languages.includes(l);
                    return (
                      <button
                        key={l}
                        onClick={() => toggleLang(l)}
                        className={`py-2 px-3.5 rounded-full border text-xs font-semibold transition-all duration-200 ${
                          active 
                            ? 'border-brand-gold bg-brand-gold text-black font-bold' 
                            : 'border-white/5 bg-white/5 text-brand-secText hover:text-white hover:border-white/20'
                        }`}
                      >
                        {l}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Runtimes */}
              <div className="space-y-3">
                <h3 className="text-xs font-extrabold text-brand-secText uppercase tracking-wider">Preferred Movie Length</h3>
                <div className="flex flex-col space-y-2">
                  {["Under 90 mins", "90-120 mins", "Over 2 hours"].map((t) => (
                    <button
                      key={t}
                      onClick={() => setRuntime(t)}
                      className={`w-full py-3 px-4 rounded-xl border text-left text-xs font-bold transition-all duration-200 flex justify-between items-center ${
                        runtime === t 
                          ? 'border-brand-gold bg-brand-gold/15 text-brand-text' 
                          : 'border-white/5 bg-white/5 text-brand-secText hover:border-white/20'
                      }`}
                    >
                      <span>{t}</span>
                      {runtime === t && <CheckCircle className="w-4 h-4 text-brand-gold fill-brand-gold/10" />}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-xl sm:text-2xl font-bold text-brand-text flex items-center font-serif uppercase tracking-tight">
                <Compass className="w-5 h-5 text-brand-gold mr-2" />
                Choose Your Mood
              </h2>
              <p className="text-xs text-brand-secText">Select what matches your mindset right now to shape instant recommendations.</p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {moodOptions.map((m) => (
                <button
                  key={m.val}
                  onClick={() => setMood(m.val)}
                  className={`py-4 px-4 rounded-xl border text-xs font-bold transition-all duration-300 flex flex-col items-center justify-center space-y-2 text-center ${
                    mood === m.val 
                      ? 'border-brand-gold bg-brand-gold/15 text-brand-text glow-gold' 
                      : 'border-white/5 bg-white/5 text-brand-secText hover:border-white/20'
                  }`}
                >
                  <span className="text-xl">{m.label.split(' ')[0]}</span>
                  <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wide">{m.label.split(' ').slice(1).join(' ')}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Buttons Controls */}
        <div className="flex items-center justify-between pt-6 border-t border-white/5">
          {step > 1 ? (
            <button
              onClick={() => setStep(step - 1)}
              className="flex items-center space-x-1 text-xs font-black text-brand-secText hover:text-white uppercase transition"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
          ) : (
            <div></div>
          )}

          {step < 4 ? (
            <button
              onClick={() => setStep(step + 1)}
              className="flex items-center space-x-1 bg-brand-gold hover:bg-brand-lightgold text-black text-xs font-black px-5 py-2.5 rounded shadow-lg uppercase transition"
            >
              <span>Next</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              className="flex items-center space-x-2 bg-brand-gold hover:bg-brand-lightgold text-black text-xs font-black px-6 py-3 rounded shadow-xl uppercase transition glow-gold"
            >
              <Sparkles className="w-4 h-4 fill-current animate-spin" style={{ animationDuration: '3s' }} />
              <span>Generate Profile</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
