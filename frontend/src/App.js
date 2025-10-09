import React, { useEffect, useState } from 'react';
import api from './api';

function App(){
  const [status, setStatus] = useState('Checking backend...');
  const [symptoms, setSymptoms] = useState('fever,cough');
  const [prediction, setPrediction] = useState(null);
  const [chatInput, setChatInput] = useState('');
  const [chatResponse, setChatResponse] = useState('');

  useEffect(()=>{ async function chk(){ try{ const r=await api.getHealth(); if(r && r.status==='ok') setStatus('✅ Backend connected'); else setStatus('❌ Backend unexpected'); }catch(e){ setStatus('❌ Backend not reachable'); } } chk(); },[]);

  const runPredict = async ()=>{
    const list = symptoms.split(',').map(s=>s.trim()).filter(Boolean);
    const res = await api.predict(list);
    setPrediction(res);
  };

  const sendChat = async ()=>{
    const res = await api.chat({message: chatInput});
    setChatResponse(res.response||JSON.stringify(res));
  };

  return (
    <div className="app">
      <header><h1>MediAssist Dashboard</h1><div>{status}</div></header>
      <div className="grid">
        <main>
          <div className="card">
            <h2>Symptom Checker</h2>
            <p>Enter symptoms (comma separated)</p>
            <input style={{width:'100%',padding:8}} value={symptoms} onChange={e=>setSymptoms(e.target.value)} />
            <div style={{marginTop:8}}>
              <button onClick={runPredict}>Predict</button>
            </div>
            {prediction && <pre style={{marginTop:8}}>{JSON.stringify(prediction,null,2)}</pre>}
          </div>

          <div className="card">
            <h2>Chatbot</h2>
            <input style={{width:'100%',padding:8}} value={chatInput} onChange={e=>setChatInput(e.target.value)} placeholder="Describe your issue" />
            <div style={{marginTop:8}}><button onClick={sendChat}>Send</button></div>
            {chatResponse && <p style={{marginTop:8}}>{chatResponse}</p>}
          </div>
        </main>

        <aside>
          <div className="card">
            <h3>Quick Actions</h3>
            <p>Register / Login via API</p>
          </div>
          <div className="card">
            <h3>Appointments</h3>
            <p>Book via API</p>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default App;
