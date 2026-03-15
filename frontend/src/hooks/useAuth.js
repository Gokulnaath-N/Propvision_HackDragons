import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import authApi from '../services/authApi';

export function useAuth() {
  const { user, setUser } = useContext(AuthContext);

  const login = async (email, password) => {
    const res = await authApi.login(email, password);
    localStorage.setItem('pv_token', res.access_token);
    setUser(res.user);
    return res.user;
  };

  const signup = async (formData) => {
    const res = await authApi.signup(formData);
    localStorage.setItem('pv_token', res.access_token);
    setUser(res.user);
    return res.user;
  };

  const logout = () => {
    localStorage.removeItem('pv_token');
    setUser(null);
  };

  const isAuthenticated = !!user;
  const isBroker = user?.role === 'broker';
  const isUser   = user?.role === 'user';

  return { 
    user, 
    login, 
    signup, 
    logout,
    isAuthenticated, 
    isBroker, 
    isUser 
  };
}
