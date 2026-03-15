import React, { useEffect, useState } from 'react';
import { Plus, History, Compass, User, ChevronRight } from 'lucide-react';
import { getDiscoverItems, getHistory } from '../services/api';
import gsap from 'gsap';

const Sidebar = ({ isOpen, setQuery }) => {
  const [discoverItems, setDiscoverItems] = useState([]);
  const [historyItems, setHistoryItems] = useState([]);

  useEffect(() => {
    // Fetch Discover and History on mount
    const fetchData = async () => {
      const [discoverData, historyData] = await Promise.all([
        getDiscoverItems(),
        getHistory()
      ]);
      setDiscoverItems(discoverData);
      setHistoryItems(historyData);
    };
    fetchData();
  }, []);

  useEffect(() => {
    if (isOpen) {
      gsap.to('.sidebar-panel', { x: 0, duration: 0.4, ease: 'power3.out' });
      gsap.fromTo('.sidebar-item', 
        { autoAlpha: 0, x: -10 }, 
        { autoAlpha: 1, x: 0, duration: 0.3, stagger: 0.05, ease: 'power2.out', delay: 0.1 }
      );
    } else {
      gsap.to('.sidebar-panel', { x: '-100%', duration: 0.4, ease: 'power3.in' });
    }
  }, [isOpen]);

  return (
    <aside className="sidebar-panel fixed lg:relative z-40 w-[280px] h-full bg-background border-r border-border flex flex-col shrink-0 flex-shrink-0 -translate-x-full lg:translate-x-0 transition-transform lg:transition-none duration-300">
      
      {/* Top Section */}
      <div className="p-4 border-b border-border">
        <button 
          onClick={() => setQuery('')}
          className="sidebar-item w-full flex items-center justify-between px-4 py-3 rounded-xl bg-panel hover:bg-panelHover transition-colors border border-border group"
        >
          <div className="flex items-center gap-3 text-sm font-medium text-textPrimary">
            <Plus size={18} className="text-textSecondary group-hover:text-textPrimary transition-colors" />
            New Search
          </div>
          <ChevronRight size={16} className="text-textSecondary opacity-0 group-hover:opacity-100 transition-opacity" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto hide-scrollbar p-4 space-y-8">
        
        {/* History Section */}
        {historyItems.length > 0 && (
          <div className="sidebar-item space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-textSecondary px-2 uppercase tracking-whider">
              <History size={14} />
              Recent Searches
            </div>
            <div className="space-y-1">
              {historyItems.map((item) => (
                <button
                  key={`history-${item.id}`}
                  onClick={() => setQuery(item.query)}
                  className="sidebar-item w-full text-left px-3 py-2 text-sm text-textSecondary hover:text-textPrimary hover:bg-panel rounded-lg truncate transition-colors"
                >
                  {item.query}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Discover Section */}
        <div className="sidebar-item space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-textSecondary px-2 uppercase tracking-whider">
            <Compass size={14} />
            Discover Styles
          </div>
          <div className="grid grid-cols-2 gap-2">
            {discoverItems.map((item) => (
              <button
                key={`discover-${item.id}`}
                onClick={() => setQuery(item.title)}
                className="sidebar-item relative group aspect-square rounded-xl overflow-hidden border border-border bg-panel"
              >
                <img 
                  src={item.image} 
                  alt={item.title} 
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-background/40 to-transparent"></div>
                <div className="absolute bottom-0 left-0 p-2 w-full">
                  <p className="text-[10px] font-medium text-textPrimary leading-tight line-clamp-2">
                    {item.title}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>

      </div>

      {/* Bottom Section */}
      <div className="sidebar-item p-4 border-t border-border mt-auto">
        <button className="w-full flex items-center gap-3 px-2 py-2 rounded-xl hover:bg-panel transition-colors">
          <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary border border-primary/30">
            <User size={16} />
          </div>
          <div className="text-sm font-medium text-textPrimary text-left">
            D. Architect
            <p className="text-xs text-textSecondary font-normal">Pro Plan</p>
          </div>
        </button>
      </div>

    </aside>
  );
};

export default Sidebar;
