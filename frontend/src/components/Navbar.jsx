import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home as HomeIcon, LogOut, Search, Bookmark, LayoutDashboard, PlusCircle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import AuthModal from './AuthModal';

const Navbar = () => {
  const { user, logout, isAuthenticated, isBroker } = useAuth() || {};
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authTab, setAuthTab] = useState('login');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const handleOpenAuthEvent = (e) => {
      setAuthTab(e.detail || 'login');
      setIsAuthModalOpen(true);
    };
    window.addEventListener('open-auth-modal', handleOpenAuthEvent);
    
    // Check for navigation state requesting auth
    if (location.state?.openAuth) {
      setIsAuthModalOpen(true);
      // Clear state so it doesn't reopen on refresh
      navigate(location.pathname, { replace: true, state: {} });
    }

    return () => window.removeEventListener('open-auth-modal', handleOpenAuthEvent);
  }, [location, navigate]);

  const handleOpenAuth = (tab) => {
    setAuthTab(tab);
    setIsAuthModalOpen(true);
  };

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 px-8 py-6 backdrop-blur-lg bg-background/50 border-b border-border">
        <div className="max-w-5xl mx-auto flex items-center justify-between w-full">
          
          {/* Logo */}
          <Link to="/" className="nav-logo flex items-center gap-2 text-textPrimary no-underline">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <HomeIcon size={18} className="text-white" />
            </div>
            <span className="font-semibold text-xl tracking-tight">PropVision AI</span>
          </Link>

          {/* Links */}
          <div className="nav-links hidden md:flex items-center gap-8 text-sm font-medium text-textSecondary">
            <a href="#features" className="hover:text-textPrimary transition-colors">Features</a>
            <a href="#discover" className="hover:text-textPrimary transition-colors">Discover</a>
            <a href="#about" className="hover:text-textPrimary transition-colors">About</a>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-6 text-sm font-medium">
            {!isAuthenticated ? (
              <>
                <button 
                  onClick={() => handleOpenAuth('login')}
                  className="nav-cta text-textSecondary hover:text-textPrimary transition-colors cursor-pointer bg-transparent border-none"
                >
                  Log in
                </button>
                <button
                  onClick={() => handleOpenAuth('user')} 
                  className="px-5 py-2.5 rounded-full bg-textPrimary text-background font-semibold hover:bg-accent hover:text-background transition-all border-none cursor-pointer"
                  style={{ background: 'linear-gradient(135deg, #3B6FFF 0%, #00C8E0 100%)', color: 'white' }}
                >
                  Sign up
                </button>
              </>
            ) : (
              <div className="relative">
                <button 
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  className="flex items-center gap-2 bg-transparent border-none cursor-pointer focus:outline-none"
                >
                  <div 
                    className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold text-sm relative"
                    style={{ 
                      backgroundColor: '#1E293B',
                      border: `2px solid ${isBroker ? '#00C8E0' : '#3B6FFF'}` 
                    }}
                  >
                    {user?.avatar_initials || 'U'}
                    {isBroker && (
                      <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-[#00C8E0] text-[#02040F] flex items-center justify-center text-[10px] font-bold border border-[#02040F]">
                        B
                      </div>
                    )}
                  </div>
                  <span className="text-textPrimary hidden sm:block">{user?.name?.split(' ')[0]}</span>
                </button>

                {dropdownOpen && (
                  <>
                    <div 
                      className="fixed inset-0 z-40" 
                      onClick={() => setDropdownOpen(false)}
                    />
                    <div className="absolute right-0 mt-3 w-48 bg-[#0A0E20] border border-white/10 rounded-xl shadow-xl z-50 overflow-hidden py-1">
                      <div className="px-4 py-2 border-b border-white/10 mb-1">
                        <p className="text-sm text-white font-medium truncate">{user?.name}</p>
                        <p className="text-xs text-white/50 truncate">{user?.email}</p>
                      </div>
                      
                      {isBroker ? (
                        <>
                          <Link to="/broker" className="flex items-center gap-3 px-4 py-2 text-sm text-white/80 hover:text-white hover:bg-white/5 transition-colors no-underline">
                            <LayoutDashboard size={16} /> Dashboard
                          </Link>
                          <Link to="/broker" className="flex items-center gap-3 px-4 py-2 text-sm text-white/80 hover:text-white hover:bg-white/5 transition-colors no-underline">
                            <PlusCircle size={16} /> My Listings
                          </Link>
                        </>
                      ) : (
                        <>
                          <button className="w-full flex items-center gap-3 px-4 py-2 text-sm text-white/80 hover:text-white hover:bg-white/5 transition-colors border-none bg-transparent cursor-pointer text-left">
                            <Search size={16} /> My Searches
                          </button>
                          <button className="w-full flex items-center gap-3 px-4 py-2 text-sm text-white/80 hover:text-white hover:bg-white/5 transition-colors border-none bg-transparent cursor-pointer text-left">
                            <Bookmark size={16} /> Saved
                          </button>
                        </>
                      )}
                      
                      <div className="h-px bg-white/10 my-1"></div>
                      <button 
                        onClick={() => {
                          logout();
                          setDropdownOpen(false);
                        }}
                        className="w-full flex items-center gap-3 px-4 py-2 text-sm text-[#F87171] hover:bg-white/5 transition-colors border-none bg-transparent cursor-pointer text-left"
                      >
                        <LogOut size={16} /> Log out
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </nav>

      <AuthModal 
        isOpen={isAuthModalOpen} 
        onClose={() => setIsAuthModalOpen(false)} 
        initialTab={authTab}
      />
    </>
  );
};

export default Navbar;
