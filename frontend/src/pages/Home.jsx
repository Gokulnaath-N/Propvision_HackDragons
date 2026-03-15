import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';
import Navbar from '../components/Navbar';
import { Search, ChevronRight } from 'lucide-react';
import './Home.css';

gsap.registerPlugin(ScrollTrigger);

const particleTypes = {
  A: { radius: [1.5, 3], color: 'rgba(59, 111, 255, 0.7)', glow: 6, count: 25 },
  B: { radius: [1, 2], color: 'rgba(0, 200, 224, 0.6)', glow: 4, count: 20 },
  C: { radius: [2, 4], color: 'rgba(240, 165, 0, 0.5)', glow: 8, count: 15 }
};

class Particle {
  constructor(canvas, type) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.type = type;
    this.config = particleTypes[type];
    this.radius = Math.random() * (this.config.radius[1] - this.config.radius[0]) + this.config.radius[0];
    this.x = Math.random() * canvas.width;
    this.y = Math.random() * canvas.height;
    this.phase = Math.random() * Math.PI * 2;
    this.speed = Math.random() * 0.5 + 0.1;
    this.vx = (Math.random() - 0.5) * 0.5;
    this.vy = type === 'C' ? this.speed * 0.5 : type === 'A' ? -this.speed : (Math.random() - 0.5) * 0.2;
  }

  update() {
    this.phase += 0.02;
    if (this.type === 'A') {
      this.x += Math.sin(this.phase) * 0.5 + this.vx;
    } else if (this.type === 'C') {
      this.x += Math.sin(this.phase) * 0.3 + this.vx;
    } else {
      this.x += this.vx;
    }
    this.y += this.vy;
    if (this.x < 0) this.x = this.canvas.width;
    if (this.x > this.canvas.width) this.x = 0;
    if (this.y < 0) this.y = this.canvas.height;
    if (this.y > this.canvas.height) this.y = 0;
  }

  draw() {
    this.ctx.beginPath();
    this.ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    let alpha = 1;
    if (this.type === 'B') {
        alpha = Math.abs(Math.sin(this.phase)) * 0.8 + 0.2;
    }
    this.ctx.fillStyle = this.config.color.replace(/[\d.]+\)$/g, `${alpha})`);
    this.ctx.shadowBlur = this.config.glow;
    this.ctx.shadowColor = this.config.color;
    this.ctx.fill();
    this.ctx.shadowBlur = 0;
  }
}

const Home = () => {
  const navigate = useNavigate();
  const particleCanvasRef = useRef(null);
  const houseWrapRef = useRef(null);
  const [activePhase, setActivePhase] = useState(0);

  useState(() => {
    const link = document.createElement('link');
    link.href = 'https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400&family=JetBrains+Mono:wght@500&family=Syne:wght@800&display=swap';
    link.rel = 'stylesheet';
    document.head.appendChild(link);
  });

  useGSAP(() => {
    const heroTl = gsap.timeline({ defaults: { ease: "power3.out" } });
    
    const textEl = document.querySelector('.hero-headline');
    if (textEl && !textEl.querySelector('.word')) {
        const words = textEl.innerText.split(' ');
        textEl.innerHTML = words.map(w => `<span class="word inline-block">${w}</span>`).join(' ');
    }

    heroTl.from(".nav-logo", { y: -30, opacity: 0, duration: 0.7 })
          .from(".nav-links a", { y: -20, opacity: 0, stagger: 0.08, duration: 0.5 }, "-=0.4")
          .from(".nav-cta", { y: -20, opacity: 0, duration: 0.5 }, "-=0.3")
          .from(".eyebrow", { y: 40, opacity: 0, duration: 0.7, ease: "power4.out" }, "-=0.2")
          .from(".hero-headline .word", {
            y: 80, opacity: 0, rotationX: -40,
            stagger: 0.12, duration: 0.9,
            ease: "power4.out", transformOrigin: "0% 50%"
          }, "-=0.4")
          .from(".hero-sub", { y: 30, opacity: 0, duration: 0.6 }, "-=0.5")
          .from(".tag", { y: 20, opacity: 0, scale: 0.9, stagger: 0.1, duration: 0.5 }, "-=0.4");

    const pCanvas = particleCanvasRef.current;
    if (pCanvas) {
      pCanvas.width = window.innerWidth;
      pCanvas.height = window.innerHeight;
      const ctx = pCanvas.getContext('2d');
      ctx.globalCompositeOperation = "screen";

      const particles = [];
      Object.keys(particleTypes).forEach(type => {
        for (let i = 0; i < particleTypes[type].count; i++) {
          particles.push(new Particle(pCanvas, type));
        }
      });

      let rAF;
      const renderParticles = () => {
        ctx.clearRect(0, 0, pCanvas.width, pCanvas.height);
        particles.forEach(p => { p.update(); p.draw(); });
        rAF = requestAnimationFrame(renderParticles);
      };
      renderParticles();
      
      return () => {
        if(rAF) cancelAnimationFrame(rAF);
      };
    }
  }); // Un-scoped so it can find Navbar
  
  // Independent scope for the actual animation setup so we don't return early due to particle setup
  useGSAP(() => {
    gsap.to("#orb1", { x: "+=40", y: "+=30", duration: 6, repeat: -1, yoyo: true, ease: "sine.inOut" });
    gsap.to("#orb1", { scale: 1.15, duration: 4, repeat: -1, yoyo: true, ease: "sine.inOut" });
    gsap.to("#orb2", { x: "-=30", y: "+=50", duration: 7.5, repeat: -1, yoyo: true, ease: "sine.inOut", delay: 1.5 });
    gsap.to("#orb3", { x: "+=50", y: "-=25", duration: 5.5, repeat: -1, yoyo: true, ease: "sine.inOut", delay: 0.8 });

    document.querySelectorAll('.btn-primary, .nav-cta, .btn-ghost').forEach(btn => {
      btn.addEventListener('mousemove', (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        gsap.to(btn, { x: x * 0.35, y: y * 0.35, duration: 0.4, ease: "power2.out" });
      });
      btn.addEventListener('mouseleave', () => {
        gsap.to(btn, { x: 0, y: 0, duration: 0.6, ease: "elastic.out(1, 0.4)" });
      });
    });

    document.querySelectorAll('.nav-links a').forEach(link => {
      const underline = document.createElement('span');
      underline.style.cssText = `position:absolute; bottom:-2px; left:0; width:0; height:1px; background:linear-gradient(90deg,#3B6FFF,#00C8E0);`;
      link.style.position = 'relative';
      link.appendChild(underline);
      link.addEventListener('mouseenter', () => gsap.to(underline, { width: '100%', duration: 0.3, ease: "power2.out" }));
      link.addEventListener('mouseleave', () => gsap.to(underline, { width: '0%', duration: 0.3, ease: "power2.in" }));
    });

    const scrollTl = gsap.timeline({
      scrollTrigger: {
        trigger: "#sticky-stage-wrap",
        start: "top top",
        end: "+=4000",
        scrub: true,
        pin: true,
        onUpdate: (self) => {
            gsap.to(".progress-bar", { width: self.progress * 100 + "%", duration: 0.05 });
            const p = self.progress;
            let phase = 0;
            if (p > 0.15 && p <= 0.40) phase = 1;
            if (p > 0.40 && p <= 0.65) phase = 2;
            if (p > 0.65 && p <= 0.82) phase = 3;
            if (p > 0.82) phase = 4;
            setActivePhase(phase);
        }
      }
    });

    scrollTl.to(".grid-overlay", { opacity: 0.4, duration: 25 }, 15)
            .to("#orb1", { opacity: 0.3, duration: 10 }, 15)
            .to("#orb2", { opacity: 0.8, y: "-=100", duration: 25 }, 15)
            .fromTo(".copy-phase-1", { opacity: 0, x: -50 }, { opacity: 1, x: 0, duration: 10 }, 15)
            .fromTo(".arch-label.left", { opacity: 0, x: -30 }, { opacity: 1, x: 0, duration: 10, stagger: 2 }, 15)
            .fromTo(".arch-label.right", { opacity: 0, x: 30 }, { opacity: 1, x: 0, duration: 10, stagger: 2 }, 15);

    scrollTl.to(".grid-overlay", { opacity: 0.55, duration: 25 }, 40)
            .to(".copy-phase-1", { opacity: 0, x: -50, duration: 10 }, 40)
            .fromTo(".copy-phase-2", { opacity: 0, x: 50 }, { opacity: 1, x: 0, duration: 15 }, 45)
            .to("#orb3", { opacity: 0.8, y: "-=50", duration: 15 }, 40);

    scrollTl.to(".copy-phase-2", { opacity: 0, x: 50, duration: 10 }, 65)
            .fromTo(".copy-phase-3", { opacity: 0, x: -50 }, { opacity: 1, x: 0, duration: 10 }, 65);

    scrollTl.to(".grid-overlay", { opacity: 0, duration: 18 }, 82)
            .to(".copy-phase-3", { opacity: 0, duration: 5 }, 82)
            .to(".arch-label", { opacity: 0, duration: 5 }, 82)
            .to("#orb2", { opacity: 0, duration: 5 }, 82)
            .to("#orb3", { opacity: 0, duration: 5 }, 82)
            .to("#orb1", { opacity: 1, duration: 10 }, 82)
            .fromTo(".copy-phase-4", { opacity: 0, scale: 0.9, y: 30 }, { opacity: 1, scale: 1, y: 0, duration: 10 }, 85);

    let countersFired = false;
    ScrollTrigger.create({
      trigger: "#stats-row",
      start: "top bottom",
      onEnter: () => {
        if (countersFired) return;
        countersFired = true;
        const targets = [
          { el: "#stat-upscale", end: 4, suffix: "×" },
          { el: "#stat-dims", end: 512, suffix: "" },
          { el: "#stat-stages", end: 6, suffix: "" },
          { el: "#stat-rooms", end: 10, suffix: "" },
        ];
        targets.forEach(t => {
          gsap.fromTo({ val: 0 }, { val: 0 }, {
            val: t.end, duration: 1.8, ease: "power2.out",
            onUpdate: function() {
              const dom = document.querySelector(t.el);
              if (dom) dom.textContent = Math.round(this.targets()[0].val) + t.suffix;
            }
          });
        });
      }
    });

    const wrap = houseWrapRef.current;
    if (wrap) {
      const handleMouseMove = (e) => {
        const cx = (e.clientX / window.innerWidth - 0.5) * 2;
        const cy = (e.clientY / window.innerHeight - 0.5) * 2;
        gsap.to(wrap, { rotationY: cx * 3, rotationX: -cy * 2, duration: 0.8, ease: "power2.out" });
        gsap.to("#orb1", { x: "+=" + (cx * 20), y: "+=" + (cy * 20), duration: 2 });
      };
      document.addEventListener('mousemove', handleMouseMove);
      return () => document.removeEventListener('mousemove', handleMouseMove);
    }

  }, []); // Full scope

  useGSAP(() => {
    gsap.from(".feature-card", {
      scrollTrigger: {
        trigger: ".feature-grid",
        start: "top 80%",
        end: "bottom 60%",
      },
      y: 60, opacity: 0, scale: 0.95,
      stagger: 0.15, duration: 0.8, ease: "power3.out"
    });

    gsap.from(".feat-icon", {
      scrollTrigger: { trigger: ".feature-grid", start: "top 75%" },
      scale: 0, rotation: -45, opacity: 0, stagger: 0.15, duration: 0.6, delay: 0.3, ease: "back.out(2)"
    });
  });

  return (
    <div className="home-container relative">
      <div className="progress-bar" />
      <Navbar />

      <svg className="noise-grain w-full h-full">
        <filter id="noise">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" stitchTiles="stitch"/>
        </filter>
        <rect width="100%" height="100%" filter="url(#noise)"/>
      </svg>

      <div className="fixed right-6 top-1/2 -translate-y-1/2 flex flex-col gap-4 z-50">
        {[0,1,2,3,4].map(idx => (
          <div key={idx} className={`phase-dot ${activePhase === idx ? 'active' : ''}`} />
        ))}
      </div>

      <div id="sticky-stage-wrap" className="h-[500vh]">
        <div className="sticky top-0 h-screen w-full overflow-hidden flex items-center justify-center pt-16 box-border">
          
          <div className="grid-overlay" />
          <canvas ref={particleCanvasRef} className="absolute inset-0 pointer-events-none z-10" />

          <div id="orb1" className="orb" />
          <div id="orb2" className="orb" />
          <div id="orb3" className="orb" />

          <div ref={houseWrapRef} className="relative w-full h-full flex items-center justify-center z-20" style={{ perspective: '800px' }}>
            
            <div className={`absolute inset-0 flex flex-col items-center justify-center text-center px-4 transition-opacity duration-500 pointer-events-none ${activePhase > 0 ? 'opacity-0' : 'opacity-100'}`}>
              <div className="eyebrow mono-font text-[10px] md:text-[11px] text-[var(--home-cyan)] tracking-widest mb-6">
                NEXT-GENERATION PROPERTY DISCOVERY
              </div>
              <h1 className="hero-headline display-font text-[clamp(56px,7.5vw,100px)] text-white leading-none mb-6 max-w-5xl">
                Prop<span className="text-blue-grad">Vision</span> AI
              </h1>
              <p className="hero-sub body-font text-[15px] md:text-[17px] text-[var(--home-white90)] max-w-2xl mb-12">
                Search properties the way you think about them.
              </p>
              <div className="flex flex-wrap gap-4 justify-center">
                <span className="tag mono-font text-[11px] px-4 py-2 rounded-full border border-[var(--home-blue)] text-[var(--home-blue)] bg-[var(--home-blue-glow)]">Real-ESRGAN Enhancement</span>
                <span className="tag mono-font text-[11px] px-4 py-2 rounded-full border border-[var(--home-cyan)] text-[var(--home-cyan)] bg-[var(--home-cyan-glow)]">CLIP Semantic Search</span>
                <span className="tag mono-font text-[11px] px-4 py-2 rounded-full border border-[var(--home-amber)] text-[var(--home-amber)] bg-[var(--home-amber-glow)]">Claude AI Analysis</span>
              </div>
              <div className="mt-10 z-50 animate-in fade-in slide-in-from-bottom-5 duration-700 delay-300">
                <button 
                  onClick={() => navigate('/chat')} 
                  className="px-10 py-4 rounded-full font-bold text-white transition-all transform hover:scale-105 hover:shadow-[0_0_30px_rgba(59,111,255,0.4)] pointer-events-auto cursor-pointer flex items-center gap-3 active:scale-95"
                  style={{ background: 'linear-gradient(135deg, #3B6FFF 0%, #00C8E0 100%)' }}
                >
                  <Search size={18} />
                  Explore Platform
                  < ChevronRight size={18} />
                </button>
              </div>
            </div>

            <div className="absolute left-[10%] top-1/3 flex flex-col gap-24 z-30 pointer-events-none">
              <div className="arch-label left"><div className="line" />ROOF STRUCTURE</div>
              <div className="arch-label left"><div className="line" />ATTIC FLOOR</div>
              <div className="arch-label left"><div className="line" />GROUND FLOOR</div>
            </div>

            <div className="absolute right-[10%] top-1/3 flex flex-col gap-32 z-30 pointer-events-none">
              <div className="arch-label right align-end"><div className="line" />CHIMNEY</div>
              <div className="arch-label right"><div className="line" />UPPER FLOOR</div>
              <div className="arch-label right"><div className="line" />FOUNDATION</div>
            </div>                        <div className="copy-phase-1 absolute left-[8%] md:left-[15%] top-[40%] max-w-[300px] text-left opacity-0 pointer-events-none z-40">
               <div className="mono-font text-[10px] text-[var(--home-cyan)] mb-2">VISION INTELLIGENCE</div>
               <h2 className="display-font text-3xl md:text-4xl mb-4 leading-tight">AI sees beyond the <span className="text-blue-grad">surface.</span></h2>
               <p className="body-font text-sm text-[var(--home-white60)] leading-relaxed">
                 Every uploaded image is intercepted, enhanced through Real-ESRGAN super-resolution, and analysed layer by layer — before a listing ever goes live.
               </p>
             </div>
 
             <div className="copy-phase-2 absolute right-[8%] md:right-[15%] top-[40%] max-w-[300px] text-left opacity-0 pointer-events-none z-40">
               <div className="mono-font text-[10px] text-[var(--home-amber)] mb-2">STRUCTURAL PRECISION</div>
               <h2 className="display-font text-3xl md:text-4xl mb-4 leading-tight">Intelligence in every <span className="text-amber-grad">layer.</span></h2>
               <p className="body-font text-sm text-[var(--home-white60)] leading-relaxed">
                 Rooms classified. Quality scored. Objects detected. CLIP embeddings generated. Six pipeline stages — automated, instant, invisible to the broker.
               </p>
             </div>
 
              <div className="copy-phase-3 absolute left-[8%] md:left-[15%] top-[40%] max-w-[300px] text-left opacity-0 pointer-events-none z-40">
               <div className="mono-font text-[10px] text-[var(--home-cyan)] mb-2">SEARCH AS YOU THINK</div>
               <h2 className="display-font text-3xl md:text-4xl mb-4 leading-tight">Every room <span className="text-cyan-grad">understood.</span></h2>
               <p className="body-font text-sm text-[var(--home-white60)] leading-relaxed">
                 Type '2BHK near school Vastu compliant' — Claude extracts intent, CLIP finds visual matches. Results that actually look like what you asked for.
               </p>
             </div>

            <div className="copy-phase-4 absolute inset-0 flex flex-col justify-center items-center text-center opacity-0 z-50 pointer-events-none">
              <div className="mono-font text-[10px] text-[var(--home-cyan)] mb-4">THE FUTURE OF REAL ESTATE SEARCH</div>
              <h2 className="display-font text-4xl md:text-6xl mb-6 leading-tight max-w-4xl">Where architecture meets <span className="text-blue-grad">experience.</span></h2>
              <p className="body-font text-[16px] text-[var(--home-white60)] mb-10 max-w-xl">
                A modern platform designed for how people actually search for homes.
              </p>
              <div className="flex gap-4 cursor-auto">
                <button onClick={() => navigate('/chat')} className="btn-primary px-8 py-4 pointer-events-auto cursor-pointer flex items-center gap-2">
                  Explore Platform
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </button>
                <button onClick={() => window.scrollTo(0, 0)} className="btn-ghost px-8 py-4 pointer-events-auto cursor-pointer">
                  View Architecture
                </button>
              </div>

              <div id="stats-row" className="absolute bottom-16 w-full max-w-5xl mx-auto flex justify-around border-t border-[var(--home-white10)] pt-8">
                <div className="text-center">
                  <div id="stat-upscale" className="display-font text-3xl md:text-4xl text-blue-grad mb-2">0</div>
                  <div className="mono-font text-[10px] text-[var(--home-white60)]">Image upscaling</div>
                </div>
                <div className="text-center">
                  <div id="stat-dims" className="display-font text-3xl md:text-4xl text-cyan-grad mb-2">0</div>
                  <div className="mono-font text-[10px] text-[var(--home-white60)]">CLIP Dimensions</div>
                </div>
                <div className="text-center">
                  <div id="stat-stages" className="display-font text-3xl md:text-4xl text-amber-grad mb-2">0</div>
                  <div className="mono-font text-[10px] text-[var(--home-white60)]">Pipeline Stages</div>
                </div>
                <div className="text-center">
                  <div id="stat-rooms" className="display-font text-3xl md:text-4xl text-blue-grad mb-2">0</div>
                  <div className="mono-font text-[10px] text-[var(--home-white60)]">Room Classes</div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>

      <div className="relative z-50 py-32 px-6 max-w-6xl mx-auto border-t border-[var(--home-white05)] bg-[var(--home-bg)]">
        <div className="feature-grid grid grid-cols-1 md:grid-cols-3 gap-8">
          
          <div className="feature-card p-8">
            <div className="feat-icon border border-[var(--home-blue)] bg-[var(--home-blue-glow)] text-[var(--home-blue)] mb-6">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
            </div>
            <h3 className="display-font text-xl mb-3">Image Enhancement</h3>
            <p className="body-font text-[14px] leading-relaxed text-[var(--home-white60)]">
              Real-ESRGAN runs on RTX 4050 — every blurry broker upload becomes a sharp 1920×1080 WebP automatically.
            </p>
          </div>

          <div className="feature-card p-8">
            <div className="feat-icon border border-[var(--home-cyan)] bg-[var(--home-cyan-glow)] text-[var(--home-cyan)] mb-6">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
            </div>
            <h3 className="display-font text-xl mb-3">Semantic Search</h3>
            <p className="body-font text-[14px] leading-relaxed text-[var(--home-white60)]">
              CLIP ViT-B/32 embeds every image into 512-dimensional space. Qdrant finds listings whose rooms visually match your description.
            </p>
          </div>

          <div className="feature-card p-8">
            <div className="feat-icon border border-[var(--home-amber)] bg-[var(--home-amber-glow)] text-[var(--home-amber)] mb-6">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><line x1="21.17" y1="8" x2="12" y2="8"/><line x1="3.95" y1="6.06" x2="8.54" y2="14"/><line x1="10.88" y1="21.94" x2="15.46" y2="14"/></svg>
            </div>
            <h3 className="display-font text-xl mb-3">Claude Intelligence</h3>
            <p className="body-font text-[14px] leading-relaxed text-[var(--home-white60)]">
              Claude 3.5 Sonnet parses natural language into structured intent and explains exactly why each result matches your search.
            </p>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Home;
