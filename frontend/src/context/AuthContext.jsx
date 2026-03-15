import React, { createContext, useState, useEffect } from 'react';
import authApi from '../services/authApi';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkUser = async () => {
      const token = localStorage.getItem('pv_token');
      if (token) {
        try {
          const userData = await authApi.getMe(token);
          setUser(userData);
        } catch (error) {
          console.error("Session expired or invalid token", error);
          localStorage.removeItem('pv_token');
          setUser(null);
        }
      }
      setLoading(false);
    };

    checkUser();
  }, []);

  return (
    <AuthContext.Provider value={{ user, setUser, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};
