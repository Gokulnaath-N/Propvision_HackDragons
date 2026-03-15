import React, { useState, useEffect } from 'react';
import { X, Eye, EyeOff, AlertCircle, Check, Loader2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import './AuthModal.css';

const AuthModal = ({ isOpen, onClose, initialTab = 'login' }) => {
  const [activeTab, setActiveTab] = useState(initialTab);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    phone: '',
    agency_name: '',
    city: 'Chennai',
    rera_number: '',
    agreeTerms: false,
    certifyBroker: false
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const { login, signup } = useAuth();

  useEffect(() => {
    if (isOpen) {
      setActiveTab(initialTab);
      setFormData({
        email: '', password: '', confirmPassword: '', full_name: '',
        phone: '', agency_name: '', city: 'Chennai', rera_number: '',
        agreeTerms: false, certifyBroker: false
      });
      setError('');
      setSuccess('');
      setShowPassword(false);
      
      // Prevent body scroll when modal open
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
    
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [isOpen, initialTab]);

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [onClose]);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    setError(''); // Clear error on typing
  };

  const calculatePasswordStrength = (pwd) => {
    if (!pwd) return { label: '', class: '' };
    if (pwd.length < 6) return { label: 'Too weak', class: 'pwd-weak' };
    
    let strength = 0;
    if (pwd.length >= 8) strength += 1;
    if (pwd.match(/[a-z]/) && pwd.match(/[A-Z]/)) strength += 1;
    if (pwd.match(/\d/)) strength += 1;
    if (pwd.match(/[^a-zA-Z\d]/)) strength += 1;
    
    if (strength <= 1) return { label: 'Fair', class: 'pwd-fair' };
    if (strength === 2 || strength === 3) return { label: 'Strong', class: 'pwd-strong' };
    return { label: 'Very strong', class: 'pwd-vstrong' };
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(formData.email, formData.password);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Incorrect email or password');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e, role) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const payload = {
        full_name: formData.full_name,
        email: formData.email,
        phone: formData.phone,
        password: formData.password,
        role: role
      };
      
      if (role === 'broker') {
        payload.agency_name = formData.agency_name;
        payload.city = formData.city;
        payload.rera_number = formData.rera_number;
      }
      
      await signup(payload);
      
      setSuccess(role === 'user' 
        ? 'Account created! Welcome to PropVision AI' 
        : 'Broker account created! Redirecting...'
      );
      
      setTimeout(() => {
        onClose();
        if (role === 'broker') {
          window.location.href = '/broker';
        }
      }, 1500);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const pwdObj = activeTab !== 'login' ? calculatePasswordStrength(formData.password) : null;

  const renderSuccessState = () => (
    <div className={`auth-success-state ${activeTab === 'user' ? 'success-user' : 'success-broker'}`}>
      <div className="success-icon-wrapper">
        <Check size={32} />
      </div>
      <h3 className="auth-success-title">Success!</h3>
      <p className="auth-success-desc">{success}</p>
    </div>
  );

  return (
    <div className="auth-modal-overlay" onClick={onClose}>
      <div className="auth-modal-card" onClick={e => e.stopPropagation()}>
        <button className="auth-close-btn" onClick={onClose}><X size={20} /></button>
        
        {success ? renderSuccessState() : (
          <>
            <div className="auth-modal-header">
              <div className="auth-tabs">
                <button 
                  className={`auth-tab tab-login ${activeTab === 'login' ? 'active' : ''}`}
                  onClick={() => setActiveTab('login')}
                >
                  Log in
                </button>
                <button 
                  className={`auth-tab tab-user ${activeTab === 'user' ? 'active' : ''}`}
                  onClick={() => setActiveTab('user')}
                >
                  Sign up as User
                </button>
                <button 
                  className={`auth-tab tab-broker ${activeTab === 'broker' ? 'active' : ''}`}
                  onClick={() => setActiveTab('broker')}
                >
                  Sign up as Broker
                </button>
              </div>
            </div>

            <div className="auth-modal-body">
              {error && (
                <div className="auth-error-banner">
                  <AlertCircle size={16} />
                  <span>{error}</span>
                </div>
              )}

              {/* LOG IN */}
              {activeTab === 'login' && (
                <form className="auth-form form-login" onSubmit={handleLogin}>
                  <div className="auth-input-group">
                    <label className="auth-label">Email Address</label>
                    <input 
                      type="email" name="email" className="auth-input" 
                      placeholder="Enter your email" required
                      value={formData.email} onChange={handleChange}
                    />
                  </div>
                  
                  <div className="auth-input-group">
                    <label className="auth-label">Password</label>
                    <div className="auth-password-wrapper">
                      <input 
                        type={showPassword ? "text" : "password"} name="password" className="auth-input" 
                        placeholder="••••••••" required
                        value={formData.password} onChange={handleChange}
                      />
                      <button type="button" className="auth-password-toggle" onClick={() => setShowPassword(!showPassword)}>
                        {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                    <a className="auth-link">Forgot password?</a>
                  </div>

                  <button type="submit" className="auth-btn-primary btn-login" disabled={loading}>
                    {loading ? <Loader2 className="animate-spin" size={20} /> : 'Log in'}
                  </button>

                  <div className="auth-divider">or continue with</div>

                  <button type="button" className="auth-btn-social">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                    </svg>
                    Continue with Google
                  </button>

                  <div className="auth-footer-text">
                    Don't have an account? <span className="auth-footer-link" onClick={() => setActiveTab('user')}>Sign up</span>
                  </div>
                </form>
              )}

              {/* SIGN UP AS USER */}
              {activeTab === 'user' && (
                <form className="auth-form form-user" onSubmit={(e) => handleSignup(e, 'user')}>
                  <div className="auth-role-badge badge-user">🔍 Property Seeker</div>
                  
                  <div className="auth-input-group">
                    <label className="auth-label">Full Name</label>
                    <input type="text" name="full_name" className="auth-input" placeholder="Ravi Kumar" required 
                      value={formData.full_name} onChange={handleChange} />
                  </div>
                  
                  <div className="auth-input-group">
                    <label className="auth-label">Email Address</label>
                    <input type="email" name="email" className="auth-input" placeholder="Enter your email" required 
                      value={formData.email} onChange={handleChange} />
                  </div>
                  
                  <div className="auth-input-group">
                    <label className="auth-label">Phone Number (Optional)</label>
                    <input type="tel" name="phone" className="auth-input" placeholder="+91 98765 43210" 
                      value={formData.phone} onChange={handleChange} />
                  </div>
                  
                  <div className="auth-input-group">
                    <label className="auth-label">Password</label>
                    <div className="auth-password-wrapper">
                      <input type={showPassword ? "text" : "password"} name="password" className="auth-input" placeholder="••••••••" required 
                        value={formData.password} onChange={handleChange} />
                      <button type="button" className="auth-password-toggle" onClick={() => setShowPassword(!showPassword)}>
                        {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                    {formData.password && (
                      <div className={`pwd-strength-container ${pwdObj.class}`}>
                        <div className="pwd-bars">
                          <div className="pwd-bar"></div>
                          <div className="pwd-bar"></div>
                          <div className="pwd-bar"></div>
                          <div className="pwd-bar"></div>
                        </div>
                        <span className="pwd-label">{pwdObj.label}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="auth-input-group">
                    <label className="auth-label">Confirm Password</label>
                    <input type={showPassword ? "text" : "password"} name="confirmPassword" className="auth-input" placeholder="••••••••" required 
                      value={formData.confirmPassword} onChange={handleChange} />
                  </div>

                  <label className="auth-checkbox-group">
                    <input type="checkbox" name="agreeTerms" checked={formData.agreeTerms} onChange={handleChange} required />
                    <span className="auth-checkbox-label">I agree to Terms of Service and Privacy Policy</span>
                  </label>

                  <button type="submit" className="auth-btn-primary btn-user" disabled={loading || !formData.agreeTerms}>
                    {loading ? <Loader2 className="animate-spin" size={20} /> : 'Create Account'}
                  </button>

                  <div className="auth-footer-text">
                    Already have an account? <span className="auth-footer-link" onClick={() => setActiveTab('login')}>Log in</span>
                  </div>
                </form>
              )}

              {/* SIGN UP AS BROKER */}
              {activeTab === 'broker' && (
                <form className="auth-form form-broker" onSubmit={(e) => handleSignup(e, 'broker')}>
                  <div className="auth-role-badge badge-broker">🏠 Property Broker / Mediator</div>
                  
                  <div className="auth-input-group">
                    <label className="auth-label">Full Name</label>
                    <input type="text" name="full_name" className="auth-input" placeholder="Ravi Kumar" required 
                      value={formData.full_name} onChange={handleChange} />
                  </div>

                  <div className="auth-input-group">
                    <label className="auth-label">Agency / Firm Name</label>
                    <input type="text" name="agency_name" className="auth-input" placeholder="Sri Property Consultants" required 
                      value={formData.agency_name} onChange={handleChange} />
                  </div>

                  <div className="auth-input-group">
                    <label className="auth-label">City of Operation</label>
                    <select name="city" className="auth-input" value={formData.city} onChange={handleChange} required>
                      <option value="Chennai">Chennai</option>
                      <option value="Mumbai">Mumbai</option>
                      <option value="Bangalore">Bangalore</option>
                      <option value="Hyderabad">Hyderabad</option>
                      <option value="Pune">Pune</option>
                      <option value="Delhi">Delhi</option>
                      <option value="Kolkata">Kolkata</option>
                      <option value="Coimbatore">Coimbatore</option>
                      <option value="Ahmedabad">Ahmedabad</option>
                      <option value="Surat">Surat</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>

                  <div className="auth-input-group">
                    <label className="auth-label">RERA Registration No <span style={{opacity: 0.6, textTransform: 'none'}}>(Optional but builds trust)</span></label>
                    <input type="text" name="rera_number" className="auth-input" placeholder="TN/29/Agent/..." title="Real Estate Regulatory Authority number. Helps buyers trust your listings." 
                      value={formData.rera_number} onChange={handleChange} />
                  </div>
                  
                  <div className="auth-input-group">
                    <label className="auth-label">Email Address</label>
                    <input type="email" name="email" className="auth-input" placeholder="agent@example.com" required 
                      value={formData.email} onChange={handleChange} />
                  </div>

                  <div className="auth-input-group">
                    <label className="auth-label">Phone Number</label>
                    <input type="tel" name="phone" className="auth-input" placeholder="+91 98765 43210" required 
                      value={formData.phone} onChange={handleChange} />
                  </div>
                  
                  <div className="auth-input-group">
                    <label className="auth-label">Password</label>
                    <div className="auth-password-wrapper">
                      <input type={showPassword ? "text" : "password"} name="password" className="auth-input" placeholder="••••••••" required 
                        value={formData.password} onChange={handleChange} />
                      <button type="button" className="auth-password-toggle" onClick={() => setShowPassword(!showPassword)}>
                        {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                    {formData.password && (
                      <div className={`pwd-strength-container ${pwdObj.class}`}>
                        <div className="pwd-bars">
                          <div className="pwd-bar"></div>
                          <div className="pwd-bar"></div>
                          <div className="pwd-bar"></div>
                          <div className="pwd-bar"></div>
                        </div>
                        <span className="pwd-label">{pwdObj.label}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="auth-input-group">
                    <label className="auth-label">Confirm Password</label>
                    <input type={showPassword ? "text" : "password"} name="confirmPassword" className="auth-input" placeholder="••••••••" required 
                      value={formData.confirmPassword} onChange={handleChange} />
                  </div>

                  <label className="auth-checkbox-group">
                    <input type="checkbox" name="certifyBroker" checked={formData.certifyBroker} onChange={handleChange} required />
                    <span className="auth-checkbox-label">I certify that I am a licensed property broker or mediator</span>
                  </label>

                  <button type="submit" className="auth-btn-primary btn-broker" disabled={loading || !formData.certifyBroker}>
                    {loading ? <Loader2 className="animate-spin" size={20} /> : 'Create Broker Account'}
                  </button>

                  <div className="auth-footer-text">
                    Already have an account? <span className="auth-footer-link" onClick={() => setActiveTab('login')}>Log in</span>
                  </div>
                </form>
              )}

            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AuthModal;
