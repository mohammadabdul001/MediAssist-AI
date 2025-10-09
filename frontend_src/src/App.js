import React, { useEffect, useState } from 'react';
import api from './api';

function App() {
  const [status, setStatus] = useState('Checking backend...');

  useEffect(() => {
    async function check() {
      try {
        const res = await api.getHealth();
        if (res && res.status === 'ok') {
          setStatus('✅ Backend connected');
        } else {
          setStatus('❌ Backend returned unexpected response');
        }
      } catch (err) {
        setStatus('❌ Cannot reach backend');
      }
    }
    check();
  }, []);

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', padding: 20 }}>
      <h1>MediAssist</h1>
      <p>{status}</p>
      <div style={{ marginTop: 20 }}>
        <h2>Quick Actions</h2>
        <p>Use the APIs to register, login, and run symptom predictions from the UI.</p>
      </div>
    </div>
  );
}

export default App;
