import { Routes, Route, Navigate } from 'react-router-dom';
import Home from './pages/Home';
import Chat from './pages/Chat';
import ListingDetail from './pages/ListingDetail';
import { useAuth } from './hooks/useAuth';

import BrokerUpload from './pages/BrokerUpload';

function App() {
  const { isBroker, loading } = useAuth() || { isBroker: false, loading: false };

  if (loading) return null; // Wait for auth init

  return (
    <div className="min-h-screen bg-background text-textPrimary selection:bg-primary/30">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/listing/:id" element={<ListingDetail />} />
        <Route path="/broker" element={
          isBroker
            ? <BrokerUpload />
            : <Navigate to="/" state={{ openAuth: true, authMessage: "Broker account required to access the dashboard" }} />
        }/>
      </Routes>
    </div>
  );
}

export default App;
