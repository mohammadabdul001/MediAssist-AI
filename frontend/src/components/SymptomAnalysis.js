import React, { useState, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { motion } from 'framer-motion';

const SymptomAnalysis = () => {
  const { t } = useAppContext();
  const [symptoms, setSymptoms] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);

  const commonSymptoms = [
    'Headache', 'Fever', 'Cough', 'Fatigue', 'Nausea', 'Dizziness',
    'Chest Pain', 'Shortness of Breath', 'Abdominal Pain', 'Joint Pain',
    'Rash', 'Swelling', 'Loss of Appetite', 'Insomnia', 'Anxiety'
  ];

  const handleSymptomToggle = (symptom) => {
    setSelectedSymptoms(prev => 
      prev.includes(symptom) 
        ? prev.filter(s => s !== symptom)
        : [...prev, symptom]
    );
  };

  const analyzeSymptoms = async () => {
    setLoading(true);
    // Simulate AI analysis
    setTimeout(() => {
      const mockAnalysis = {
        possibleConditions: [
          { name: 'Common Cold', probability: '75%', severity: 'Low' },
          { name: 'Seasonal Allergies', probability: '60%', severity: 'Low' },
          { name: 'Stress-related', probability: '45%', severity: 'Low' }
        ],
        recommendations: [
          'Rest and stay hydrated',
          'Monitor symptoms for 48 hours',
          'Consider over-the-counter pain relievers',
          'Seek medical attention if symptoms worsen'
        ],
        urgency: 'Low',
        nextSteps: 'Schedule a consultation if symptoms persist beyond 3 days'
      };
      setAnalysis(mockAnalysis);
      setLoading(false);
    }, 2000);
  };

  return (
    <div className="symptom-analysis">
      <div className="analysis-container">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="analysis-title"
        >
          🔍 AI Symptom Analysis
        </motion.h2>

        <div className="analysis-content">
          <div className="symptom-input-section">
            <h3>Describe Your Symptoms</h3>
            <textarea
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
              placeholder="Describe your symptoms in detail..."
              className="symptom-textarea"
            />

            <div className="common-symptoms">
              <h4>Common Symptoms (Click to select):</h4>
              <div className="symptom-tags">
                {commonSymptoms.map(symptom => (
                  <button
                    key={symptom}
                    onClick={() => handleSymptomToggle(symptom)}
                    className={`symptom-tag ${selectedSymptoms.includes(symptom) ? 'selected' : ''}`}
                  >
                    {symptom}
                  </button>
                ))}
              </div>
            </div>

            <button 
              onClick={analyzeSymptoms}
              disabled={loading || (!symptoms && selectedSymptoms.length === 0)}
              className="analyze-btn"
            >
              {loading ? 'Analyzing...' : 'Analyze Symptoms'}
            </button>
          </div>

          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="loading-analysis"
            >
              <div className="loading-spinner"></div>
              <p>AI is analyzing your symptoms...</p>
            </motion.div>
          )}

          {analysis && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="analysis-results"
            >
              <h3>Analysis Results</h3>
              
              <div className="urgency-level">
                <span className={`urgency-badge ${analysis.urgency.toLowerCase()}`}>
                  {analysis.urgency} Urgency
                </span>
              </div>

              <div className="possible-conditions">
                <h4>Possible Conditions:</h4>
                {analysis.possibleConditions.map((condition, index) => (
                  <div key={index} className="condition-item">
                    <span className="condition-name">{condition.name}</span>
                    <span className="condition-probability">{condition.probability}</span>
                    <span className={`condition-severity ${condition.severity.toLowerCase()}`}>
                      {condition.severity}
                    </span>
                  </div>
                ))}
              </div>

              <div className="recommendations">
                <h4>Recommendations:</h4>
                <ul>
                  {analysis.recommendations.map((rec, index) => (
                    <li key={index}>{rec}</li>
                  ))}
                </ul>
              </div>

              <div className="next-steps">
                <h4>Next Steps:</h4>
                <p>{analysis.nextSteps}</p>
              </div>

              <div className="action-buttons">
                <button className="btn-primary">Schedule Consultation</button>
                <button className="btn-secondary">Save Analysis</button>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SymptomAnalysis; 