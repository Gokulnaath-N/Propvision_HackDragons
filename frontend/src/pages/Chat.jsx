import React, { useState } from 'react';
import { Menu, Filter } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import SearchInterface from '../components/SearchInterface';
import FilterSidebar from '../components/FilterSidebar';
import ResultsGrid from '../components/ResultsGrid';

const Chat = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [results, setResults] = useState([]);
  const [filters, setFilters] = useState({});
  const [meta, setMeta] = useState(null);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      
      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Left Sidebar */}
      <Sidebar isOpen={isSidebarOpen} setQuery={() => {
        // Mock setQuery action on sidebar click
        if (window.innerWidth < 1024) setIsSidebarOpen(false);
      }} />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full relative z-10 overflow-hidden w-full lg:w-[calc(100%-280px)] xl:w-[calc(100%-280px-320px)] transition-all duration-300">
        
        {/* Header (Mobile Logo + Menu) */}
        <header className="flex items-center justify-between p-4 border-b border-border bg-background/50 backdrop-blur-md sticky top-0 z-20">
          
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden p-2 rounded-md hover:bg-panel transition-colors text-textSecondary"
            >
              <Menu size={20} />
            </button>
            <div className="font-semibold text-lg tracking-tight text-textPrimary select-none">
              PropVision AI
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button 
              onClick={() => setIsFilterOpen(!isFilterOpen)}
              className="xl:hidden p-2 rounded-md hover:bg-panel transition-colors text-textSecondary relative"
            >
              <Filter size={20} />
              {Object.keys(filters).length > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-primary border-2 border-background box-content"></span>
              )}
            </button>
          </div>
        </header>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto px-4 sm:px-8 py-8 md:py-12 hide-scrollbar relative z-10">
          
          <div className="max-w-5xl mx-auto flex flex-col min-h-full">
            
            {/* Search Interface Top/Center */}
            <div className="w-full relative z-20">
              <SearchInterface 
                onResults={setResults}
                onFiltersUpdate={setFilters}
                onMetaUpdate={setMeta}
              />
            </div>

            {/* Results */}
            <div className="flex-1 w-full flex flex-col relative z-10">
              <ResultsGrid results={results} meta={meta} />
            </div>

          </div>

        </div>
      </main>

      {/* Right Filter Sidebar (Always present on xl screens) */}
      <div className="hidden xl:block w-80 shrink-0 flex-shrink-0 h-full border-l border-border bg-background relative z-20">
        <FilterSidebar 
          isOpen={true} 
          onClose={() => {}} 
          filters={filters} 
          updateFilter={setFilters} 
        />
      </div>

      {/* Mobile/Tablet Filter Panel */}
      <div className="xl:hidden">
        <FilterSidebar 
          isOpen={isFilterOpen} 
          onClose={() => setIsFilterOpen(false)} 
          filters={filters} 
          updateFilter={setFilters} 
        />
      </div>

    </div>
  );
};

export default Chat;
