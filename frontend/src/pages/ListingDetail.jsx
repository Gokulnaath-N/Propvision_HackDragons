import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getListing } from '../services/api';
import Navbar from '../components/Navbar';
import { 
  ChevronLeft, 
  Share2, 
  Heart, 
  MapPin, 
  Zap, 
  Maximize2, 
  ShieldCheck, 
  Compass, 
  Info
} from 'lucide-react';
import { cn } from '../lib/utils';
import gsap from 'gsap';

export default function ListingDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeImage, setActiveImage] = useState(0);
  const [sliderPos, setSliderPos] = useState(50);

  useEffect(() => {
    async function fetchListing() {
      try {
        const data = await getListing(id);
        setListing(data);
      } catch (err) {
        console.error("Failed to fetch listing", err);
      } finally {
        setLoading(false);
      }
    }
    fetchListing();
  }, [id]);

  useEffect(() => {
    if (listing) {
      gsap.from('.reveal-item', {
        y: 20,
        opacity: 0,
        duration: 0.6,
        stagger: 0.1,
        ease: 'power3.out'
      });
    }
  }, [listing]);

  const handleSliderMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    setSliderPos(Math.min(Math.max(x, 0), 100));
  };

  if (loading) return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
    </div>
  );

  if (!listing) return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center">
      <h2 className="text-2xl font-bold text-textPrimary">Listing not found</h2>
      <button onClick={() => navigate(-1)} className="mt-4 text-primary font-medium hover:underline">Go Back</button>
    </div>
  );

  const images = [listing.hero_image, ...(listing.gallery || [])];

  return (
    <div className="min-h-screen bg-background text-textPrimary selection:bg-primary/30 pb-20">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-6 pt-24">
        {/* Navigation Actions */}
        <div className="flex items-center justify-between mb-8 reveal-item">
          <button 
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-panel hover:bg-panelHover transition-colors text-sm font-medium border border-border"
          >
            <ChevronLeft size={18} />
            Back to Results
          </button>
          <div className="flex items-center gap-3">
            <button className="p-2.5 rounded-xl bg-panel hover:bg-panelHover transition-colors border border-border">
              <Share2 size={18} />
            </button>
            <button className="p-2.5 rounded-xl bg-panel hover:bg-panelHover transition-colors border border-border">
              <Heart size={18} />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          
          {/* Left Side: Images & Intelligence */}
          <div className="lg:col-span-8 space-y-8">
            
            {/* Main Visual Section */}
            <div className="space-y-4 reveal-item">
              <div className="relative aspect-[16/10] rounded-3xl overflow-hidden bg-panel border border-border shadow-2xl">
                <img 
                  src={images[activeImage]} 
                  alt={listing.title} 
                  className="w-full h-full object-cover"
                />
                
                <div className="absolute top-6 right-6 flex flex-col gap-3">
                   <div className="px-4 py-2 rounded-full bg-background/80 backdrop-blur-md border border-border text-xs font-bold text-accent flex items-center gap-2 shadow-xl">
                      <ShieldCheck size={14} />
                      AI Verified Quality
                   </div>
                </div>
              </div>
              
              {/* Thumbnail Gallery */}
              <div className="flex gap-4 overflow-x-auto pb-2 hide-scrollbar">
                {images.map((img, i) => (
                  <button 
                    key={i}
                    onClick={() => setActiveImage(i)}
                    className={cn(
                      "relative shrink-0 w-32 aspect-video rounded-xl overflow-hidden border-2 transition-all",
                      activeImage === i ? "border-primary opacity-100" : "border-transparent opacity-60 hover:opacity-100"
                    )}
                  >
                    <img src={img} className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            </div>

            {/* AI Before/After Analysis */}
            <div className="reveal-item space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold flex items-center gap-2">
                  <Zap size={20} className="text-primary" />
                  AI Enhancement Analysis
                </h3>
                <div className="text-xs text-textSecondary flex items-center gap-1">
                  <Info size={14} />
                  Slide to compare RAW vs ENHANCED
                </div>
              </div>
              
              <div 
                className="relative aspect-video rounded-3xl overflow-hidden border border-border cursor-ew-resize group shadow-xl"
                onMouseMove={handleSliderMove}
                onTouchMove={(e) => handleSliderMove(e.touches[0])}
              >
                {/* AFTER image (Top Layer) */}
                <div 
                  className="absolute inset-0 z-10"
                  style={{ clipPath: `inset(0 0 0 ${sliderPos}%)` }}
                >
                  <img src={listing.before_after?.after} className="w-full h-full object-cover select-none" />
                  <div className="absolute top-6 right-6 px-3 py-1.5 rounded-full bg-primary text-white text-[10px] font-bold uppercase tracking-widest shadow-lg">
                    Enhanced
                  </div>
                </div>
                
                {/* BEFORE image (Bottom Layer) */}
                <div className="absolute inset-0">
                  <img src={listing.before_after?.before} className="w-full h-full object-cover select-none" />
                  <div className="absolute top-6 left-6 px-3 py-1.5 rounded-full bg-panel/80 backdrop-blur-md text-textPrimary text-[10px] font-bold uppercase tracking-widest border border-border shadow-lg">
                    Raw Input
                  </div>
                </div>

                {/* Slider bar */}
                <div 
                  className="absolute top-0 bottom-0 w-1 bg-white z-20 pointer-events-none shadow-[0_0_15px_rgba(255,255,255,0.5)]"
                  style={{ left: `${sliderPos}%` }}
                >
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-2xl border-4 border-primary">
                    <Maximize2 size={16} className="text-primary" />
                  </div>
                </div>
              </div>
            </div>

          </div>

          {/* Right Side: Details & Intelligence Stats */}
          <div className="lg:col-span-4 space-y-8">
            
            <div className="p-8 rounded-3xl bg-panel border border-border space-y-6 reveal-item shadow-xl relative overflow-hidden">
               <div className="absolute top-0 right-0 p-4">
                  <Zap size={40} className="text-primary/5 rotate-12" />
               </div>

               <div className="space-y-1">
                  <div className="flex items-center gap-2 text-primary font-bold text-sm uppercase tracking-widest mb-2">
                     <ShieldCheck size={16} />
                     Verified Listing
                  </div>
                  <h1 className="text-3xl font-bold tracking-tight">{listing.title}</h1>
                  <p className="text-textSecondary flex items-center gap-1">
                    <MapPin size={16} />
                    {listing.location}
                  </p>
               </div>

               <div className="text-4xl font-bold text-primary">
                  {listing.price}
               </div>

               <div className="pt-6 border-t border-border space-y-4">
                  <h4 className="text-sm font-semibold text-textSecondary uppercase tracking-wider">Spatial Intelligence</h4>
                  
                  <div className="grid grid-cols-2 gap-4">
                     <div className="p-4 rounded-2xl bg-background border border-border">
                        <p className="text-[10px] font-bold text-textSecondary uppercase mb-1">Clutter Score</p>
                        <div className="text-lg font-bold text-accent">{listing.intelligence?.clutter_score}% Minimal</div>
                     </div>
                     <div className="p-4 rounded-2xl bg-background border border-border">
                        <p className="text-[10px] font-bold text-textSecondary uppercase mb-1">Lighting</p>
                        <div className="text-[13px] font-bold truncate leading-tight mt-1">{listing.intelligence?.lighting}</div>
                     </div>
                     <div className="p-4 rounded-2xl bg-background border border-border col-span-2 flex items-center justify-between">
                        <div>
                           <p className="text-[10px] font-bold text-textSecondary uppercase mb-1">Vastu Compliance</p>
                           <div className="text-lg font-bold text-primary">{listing.intelligence?.vastu}</div>
                        </div>
                        <Compass className="text-primary/20" size={32} />
                     </div>
                  </div>
               </div>

               <div className="pt-6 border-t border-border space-y-4">
                  <h4 className="text-sm font-semibold text-textSecondary uppercase tracking-wider">Objects Detected</h4>
                  <div className="flex flex-wrap gap-2">
                     {listing.intelligence?.objects_detected?.map(obj => (
                        <span key={obj} className="px-3 py-1 rounded-lg bg-background text-[11px] font-medium border border-border">{obj}</span>
                     ))}
                  </div>
               </div>

               <button className="w-full py-4 rounded-2xl bg-textPrimary text-background font-bold text-lg hover:bg-accent transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-textPrimary/10">
                  Contact Property Agent
               </button>
            </div>

            <div className="p-8 rounded-3xl bg-panel border border-border reveal-item shadow-xl">
               <h4 className="text-lg font-bold mb-4">AI Analysis Summary</h4>
               <p className="text-sm text-textSecondary leading-relaxed italic">
                 "{listing.description}"
               </p>
            </div>

          </div>

        </div>
      </div>
    </div>
  );
}
