import { useState, useRef, useEffect } from 'react'
import { useSearch } from '../hooks/useSearch'
import { Plus, ChevronDown, Monitor, Mic, ArrowRight, Activity, X } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

export default function SearchInterface({ onResults, onFiltersUpdate, onMetaUpdate }) {
  const [query, setQuery] = useState('')
  const [country, setCountry] = useState('')
  const [city, setCity] = useState('')
  const [vastu, setVastu] = useState(false)
  const [searchCount, setSearchCount] = useState(() => {
    return parseInt(localStorage.getItem('pv_search_count') || '0', 10);
  });
  const [showBanner, setShowBanner] = useState(false);

  const { search, loading, results, filters,
          modelMeta, resetSearch } = useSearch()

  // Sync results back to parent
  useEffect(() => {
    if (onResults) onResults(results);
  }, [results, onResults]);

  useEffect(() => {
    if (onFiltersUpdate) onFiltersUpdate(filters);
  }, [filters, onFiltersUpdate]);

  useEffect(() => {
    if (onMetaUpdate) onMetaUpdate(modelMeta);
  }, [modelMeta, onMetaUpdate]);
  const inputRef = useRef(null)
  
  const { isAuthenticated } = useAuth() || { isAuthenticated: false };

  useEffect(() => {
    if (!isAuthenticated && searchCount >= 3 && !localStorage.getItem('pv_dismissed_banner')) {
      setShowBanner(true);
    }
  }, [searchCount, isAuthenticated]);

  const handleSearch = async () => {
    if (!isAuthenticated && searchCount >= 3) {
      setShowBanner(true);
      return; // Block further searches until logged in
    }

    let finalQuery = query.trim();
    let filterParts = [];
    if (country) filterParts.push(`Country: ${country}`);
    if (city) filterParts.push(`City: ${city}`);
    if (vastu) filterParts.push(`Vastu Compliant: Yes`);
    
    if (filterParts.length > 0 && finalQuery) {
      finalQuery = `${finalQuery} (Must match filters: ${filterParts.join(', ')})`;
    } else if (filterParts.length > 0 && !finalQuery) {
      finalQuery = `Show me properties matching: ${filterParts.join(', ')}`;
    }

    if (!finalQuery || loading) return
    
    if (!isAuthenticated) {
      const newCount = searchCount + 1;
      setSearchCount(newCount);
      localStorage.setItem('pv_search_count', newCount.toString());
    }

    const extraFilters = {
      city,
      country,
      vastu
    };
  
    await search(query || finalQuery, extraFilters)
    setQuery('')
  }

  const handleVoice = () => {
    if (!isAuthenticated && searchCount >= 3) {
      setShowBanner(true);
      return;
    }
    const recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!recognition) return alert('Speech recognition not supported in this browser.');
    
    const rec = new recognition();
    rec.lang = 'en-IN';
    
    rec.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      setQuery(transcript);
      setTimeout(() => {
        const submitBtn = document.getElementById('search-submit-btn');
        if (submitBtn) submitBtn.click();
      }, 100);
    };
    
    rec.start();
  }

  // Auto-resize textarea
  useEffect(() => {
    const el = inputRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = `${el.scrollHeight}px`
    }
  }, [query])

  return (
    <div className="w-full max-w-4xl mx-auto flex flex-col items-center">
      {/* Search Box */}
      <div 
        className="w-full bg-[#202020] border border-white/10 rounded-2xl p-3 shadow-2xl focus-within:ring-1 focus-within:ring-white/20 transition-all cursor-text flex flex-col gap-3 group relative overflow-hidden"
        onClick={() => inputRef.current?.focus()}
      >
        {/* Subtle glow effect behind input */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-1 bg-gradient-to-r from-transparent via-primary/20 to-transparent group-focus-within:via-primary/50 transition-all duration-500"></div>

        {/* Top: Input area */}
        <textarea
          ref={inputRef}
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSearch();
            }
          }}
          placeholder="Ask anything..."
          className="w-full bg-transparent text-white placeholder-white/40 outline-none resize-none overflow-hidden min-h-[44px] text-lg px-2 pt-1 rounded-t-xl font-medium"
          rows={1}
          disabled={loading}
          style={{ height: 'auto', maxHeight: '150px' }}
        />
        
        {/* Bottom: Action bar */}
        <div className="flex items-center justify-between mt-auto px-1">
          {/* Left Actions */}
          <div className="flex items-center gap-2">
            <button className="w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/70 transition-colors border border-white/5 relative group/btn">
              <Plus size={16} />
              <div className="absolute -top-8 bg-black/80 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover/btn:opacity-100 pointer-events-none transition-opacity whitespace-nowrap">
                Attach File
              </div>
            </button>
            {results?.length > 0 && (
              <button 
                onClick={(e) => { e.stopPropagation(); resetSearch(); }} 
                className="flex items-center gap-1.5 text-xs text-white/50 hover:text-white px-2 py-1 bg-white/5 rounded-full hover:bg-white/10 transition-all"
              >
                <X size={12} /> Clear Results
              </button>
            )}
          </div>
          
          {/* Right Actions */}
          <div className="flex items-center gap-3 sm:gap-4">
            
            {/* Custom Filters */}
            <div className="hidden md:flex items-center gap-4 border-r border-white/10 pr-4 mr-1">
              
              {/* Country Select */}
              <select 
                value={country}
                onChange={(e) => {
                  setCountry(e.target.value);
                  setCity(''); // Reset city when country changes
                }}
                className="bg-transparent text-sm font-medium text-white/80 hover:text-white transition-colors outline-none cursor-pointer [&>option]:bg-[#202020] [&>option]:text-white"
              >
                <option value="">Country</option>
                <option value="India">India</option>
                <option value="UAE">UAE</option>
                <option value="USA">USA</option>
              </select>

              {/* City Select */}
              <select 
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="bg-transparent text-sm font-medium text-white/80 hover:text-white transition-colors outline-none cursor-pointer [&>option]:bg-[#202020] [&>option]:text-white"
                disabled={!country}
              >
                <option value="">City</option>
                {country === 'India' && (
                  <>
                    <option value="Bangalore">Bangalore</option>
                    <option value="Mumbai">Mumbai</option>
                    <option value="Chennai">Chennai</option>
                    <option value="Delhi">Delhi</option>
                    <option value="Hyderabad">Hyderabad</option>
                  </>
                )}
                {country === 'UAE' && <option value="Dubai">Dubai</option>}
                {country === 'USA' && <option value="New York">New York</option>}
              </select>

              {/* Vastu Checkbox */}
              <label className="flex items-center gap-1.5 text-sm font-medium text-white/80 hover:text-white transition-colors cursor-pointer select-none">
                <input 
                  type="checkbox" 
                  checked={vastu}
                  onChange={(e) => setVastu(e.target.checked)}
                  className="w-3.5 h-3.5 rounded-sm border-white/30 bg-transparent text-blue-500 focus:ring-0 focus:ring-offset-0 cursor-pointer accent-blue-500 transition-colors"
                />
                Vastu
              </label>
            </div>
            <button 
              onClick={(e) => { e.stopPropagation(); handleVoice(); }} 
              className="text-white/60 hover:text-white transition-colors p-1"
            >
              <Mic size={18} />
            </button>
            <button
              id="search-submit-btn"
              onClick={(e) => { e.stopPropagation(); handleSearch(); }}
              disabled={loading}
              className={`w-9 h-9 rounded-full flex items-center justify-center transition-all duration-300 ${
                query.trim() 
                  ? 'bg-blue-600 text-white hover:bg-blue-500 shadow-[0_0_15px_rgba(37,99,235,0.4)]' 
                  : 'bg-white text-black hover:bg-gray-200'
              }`}
            >
              {loading ? (
                 <div className="w-4 h-4 border-2 border-inherit border-t-transparent rounded-full animate-spin" />
              ) : query.trim() ? (
                 <ArrowRight size={18} strokeWidth={2.5} className="animate-in slide-in-from-left-2" />
              ) : (
                 <Activity size={18} strokeWidth={2.5} />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Model indicator */}
      {modelMeta && (
        <div className="flex gap-3 mt-5 items-center justify-center opacity-80 animate-in fade-in slide-in-from-top-2 duration-500 bg-black/40 px-3 py-1.5 rounded-full border border-white/5 shadow-inner">
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase flex items-center gap-1.5 ${
            modelMeta.model_used?.includes('gemini')
              ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' 
              : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${modelMeta.model_used?.includes('gemini') ? 'bg-cyan-400' : 'bg-amber-400'}`} />
            {modelMeta.model_used?.includes('gemini')
              ? 'Gemini 2.0 Flash' : 'Llama 3.3 70B'}
          </span>
          <div className="flex items-center gap-1.5 text-xs text-white/60 font-medium font-mono border-l border-white/10 pl-3">
            {modelMeta.latency_ms}ms
          </div>
          <span className="text-xs text-white/20 hidden sm:inline-block">/</span>
          <span className="text-[10px] text-white/50 uppercase tracking-widest hidden sm:inline-block font-medium">
            {modelMeta.complexity} Query
          </span>
        </div>
      )}

      {/* Soft Signup Banner */}
      {!isAuthenticated && showBanner && (
        <div 
          className="mt-4 flex items-center justify-between w-full max-w-2xl bg-gradient-to-r from-[#0A0E20] to-[#1a2342] border border-[#3B6FFF]/30 rounded-xl p-3 px-4 shadow-lg animate-in slide-in-from-top-2 cursor-pointer hover:border-[#3B6FFF]/60 transition-colors"
          onClick={() => window.dispatchEvent(new CustomEvent('open-auth-modal', { detail: 'user' }))}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#3B6FFF]/20 flex items-center justify-center text-[#3B6FFF]">
              <Search size={16} />
            </div>
            <span className="text-sm font-medium text-white/90">
              Sign up free to save searches and see full listing details <ArrowRight size={14} className="inline ml-1" />
            </span>
          </div>
          <button 
            onClick={(e) => {
              e.stopPropagation();
              setShowBanner(false);
              localStorage.setItem('pv_dismissed_banner', 'true');
            }}
            className="p-1 rounded-full text-white/40 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  )
}
