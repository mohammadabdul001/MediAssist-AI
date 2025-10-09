import React, { useState, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { motion } from 'framer-motion';

const HealthAnalytics = () => {
  const { t } = useAppContext();
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedPeriod, setSelectedPeriod] = useState('30d');

  const healthData = {
    vitals: {
      bloodPressure: { systolic: 120, diastolic: 80, trend: 'stable' },
      heartRate: { current: 72, trend: 'normal', range: '60-100' },
      temperature: { current: 98.6, trend: 'normal', range: '97-99' },
      weight: { current: 70, trend: 'decreasing', unit: 'kg' },
      bmi: { current: 22.5, category: 'Normal', trend: 'stable' }
    },
    activities: {
      steps: { today: 8500, goal: 10000, weekly: [6500, 7200, 8100, 7800, 9200, 8500, 8500] },
      sleep: { hours: 7.5, quality: 'Good', weekly: [7, 6.5, 8, 7.5, 6, 8.5, 7.5] },
      water: { today: 2.1, goal: 2.5, unit: 'L', weekly: [2.0, 2.3, 1.8, 2.5, 2.2, 2.0, 2.1] },
      exercise: { minutes: 45, goal: 60, weekly: [30, 45, 60, 40, 55, 35, 45] }
    },
    trends: {
      mood: ['Happy', 'Stressed', 'Calm', 'Energetic', 'Tired', 'Happy', 'Calm'],
      energy: [8, 6, 7, 9, 5, 8, 7],
      stress: [3, 7, 4, 2, 6, 3, 4]
    }
  };

  const periods = [
    { value: '7d', label: '7 Days' },
    { value: '30d', label: '30 Days' },
    { value: '90d', label: '90 Days' },
    { value: '1y', label: '1 Year' }
  ];

  const getHealthScore = () => {
    const vitalsScore = 85;
    const activityScore = 78;
    const sleepScore = 82;
    const overallScore = Math.round((vitalsScore + activityScore + sleepScore) / 3);
    return overallScore;
  };

  const healthScore = getHealthScore();

  const renderProgressBar = (current, goal, color = '#2962ff') => (
    <div className="progress-container">
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ 
            width: `${Math.min((current / goal) * 100, 100)}%`,
            backgroundColor: color
          }}
        ></div>
      </div>
      <span className="progress-text">{current}/{goal}</span>
    </div>
  );

  const renderTrendIndicator = (trend) => {
    const indicators = {
      increasing: '📈',
      decreasing: '📉',
      stable: '➡️',
      normal: '✅'
    };
    return <span className="trend-indicator">{indicators[trend] || '➡️'}</span>;
  };

  return (
    <div className="health-analytics">
      <div className="analytics-container">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="analytics-title"
        >
          📊 Health Analytics
        </motion.h2>

        <div className="analytics-header">
          <div className="period-selector">
            <label>Time Period:</label>
            <select 
              value={selectedPeriod} 
              onChange={(e) => setSelectedPeriod(e.target.value)}
            >
              {periods.map(period => (
                <option key={period.value} value={period.value}>
                  {period.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="analytics-tabs">
          <button
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab ${activeTab === 'vitals' ? 'active' : ''}`}
            onClick={() => setActiveTab('vitals')}
          >
            Vitals
          </button>
          <button
            className={`tab ${activeTab === 'activities' ? 'active' : ''}`}
            onClick={() => setActiveTab('activities')}
          >
            Activities
          </button>
          <button
            className={`tab ${activeTab === 'trends' ? 'active' : ''}`}
            onClick={() => setActiveTab('trends')}
          >
            Trends
          </button>
        </div>

        <div className="analytics-content">
          {activeTab === 'overview' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="overview-dashboard"
            >
              <div className="health-score-section">
                <div className="health-score-card">
                  <h3>Overall Health Score</h3>
                  <div className="score-circle">
                    <span className="score-number">{healthScore}</span>
                    <span className="score-label">/100</span>
                  </div>
                  <p className="score-description">
                    {healthScore >= 80 ? 'Excellent' : healthScore >= 60 ? 'Good' : 'Needs Improvement'}
                  </p>
                </div>
              </div>

              <div className="quick-stats">
                <div className="stat-card">
                  <h4>Blood Pressure</h4>
                  <div className="stat-value">
                    {healthData.vitals.bloodPressure.systolic}/{healthData.vitals.bloodPressure.diastolic}
                  </div>
                  <div className="stat-trend">
                    {renderTrendIndicator(healthData.vitals.bloodPressure.trend)}
                    {healthData.vitals.bloodPressure.trend}
                  </div>
                </div>

                <div className="stat-card">
                  <h4>Heart Rate</h4>
                  <div className="stat-value">{healthData.vitals.heartRate.current} bpm</div>
                  <div className="stat-trend">
                    {renderTrendIndicator(healthData.vitals.heartRate.trend)}
                    {healthData.vitals.heartRate.trend}
                  </div>
                </div>

                <div className="stat-card">
                  <h4>BMI</h4>
                  <div className="stat-value">{healthData.vitals.bmi.current}</div>
                  <div className="stat-category">{healthData.vitals.bmi.category}</div>
                </div>

                <div className="stat-card">
                  <h4>Daily Steps</h4>
                  <div className="stat-value">{healthData.activities.steps.today}</div>
                  {renderProgressBar(healthData.activities.steps.today, healthData.activities.steps.goal)}
                </div>
              </div>

              <div className="recent-trends">
                <h3>Recent Trends</h3>
                <div className="trends-grid">
                  <div className="trend-item">
                    <h4>Sleep Quality</h4>
                    <div className="trend-chart">
                      {healthData.activities.sleep.weekly.map((hours, index) => (
                        <div 
                          key={index} 
                          className="trend-bar"
                          style={{ height: `${(hours / 10) * 100}%` }}
                          title={`${hours}h`}
                        ></div>
                      ))}
                    </div>
                  </div>

                  <div className="trend-item">
                    <h4>Water Intake</h4>
                    <div className="trend-chart">
                      {healthData.activities.water.weekly.map((liters, index) => (
                        <div 
                          key={index} 
                          className="trend-bar"
                          style={{ height: `${(liters / 3) * 100}%` }}
                          title={`${liters}L`}
                        ></div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'vitals' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="vitals-dashboard"
            >
              <h3>Vital Signs</h3>
              
              <div className="vitals-grid">
                <div className="vital-card">
                  <h4>Blood Pressure</h4>
                  <div className="vital-value">
                    {healthData.vitals.bloodPressure.systolic}/{healthData.vitals.bloodPressure.diastolic} mmHg
                  </div>
                  <div className="vital-status normal">Normal</div>
                  <div className="vital-trend">
                    {renderTrendIndicator(healthData.vitals.bloodPressure.trend)}
                    Trend: {healthData.vitals.bloodPressure.trend}
                  </div>
                </div>

                <div className="vital-card">
                  <h4>Heart Rate</h4>
                  <div className="vital-value">{healthData.vitals.heartRate.current} bpm</div>
                  <div className="vital-status normal">Normal</div>
                  <div className="vital-range">Range: {healthData.vitals.heartRate.range}</div>
                </div>

                <div className="vital-card">
                  <h4>Temperature</h4>
                  <div className="vital-value">{healthData.vitals.temperature.current}°F</div>
                  <div className="vital-status normal">Normal</div>
                  <div className="vital-range">Range: {healthData.vitals.temperature.range}</div>
                </div>

                <div className="vital-card">
                  <h4>Weight</h4>
                  <div className="vital-value">{healthData.vitals.weight.current} {healthData.vitals.weight.unit}</div>
                  <div className="vital-trend">
                    {renderTrendIndicator(healthData.vitals.weight.trend)}
                    {healthData.vitals.weight.trend}
                  </div>
                </div>

                <div className="vital-card">
                  <h4>BMI</h4>
                  <div className="vital-value">{healthData.vitals.bmi.current}</div>
                  <div className="vital-status normal">{healthData.vitals.bmi.category}</div>
                  <div className="vital-trend">
                    {renderTrendIndicator(healthData.vitals.bmi.trend)}
                    {healthData.vitals.bmi.trend}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'activities' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="activities-dashboard"
            >
              <h3>Daily Activities</h3>
              
              <div className="activities-grid">
                <div className="activity-card">
                  <h4>Steps</h4>
                  <div className="activity-value">{healthData.activities.steps.today}</div>
                  <div className="activity-goal">Goal: {healthData.activities.steps.goal}</div>
                  {renderProgressBar(healthData.activities.steps.today, healthData.activities.steps.goal, '#4caf50')}
                </div>

                <div className="activity-card">
                  <h4>Sleep</h4>
                  <div className="activity-value">{healthData.activities.sleep.hours}h</div>
                  <div className="activity-quality">{healthData.activities.sleep.quality}</div>
                  <div className="activity-goal">Goal: 8h</div>
                  {renderProgressBar(healthData.activities.sleep.hours, 8, '#9c27b0')}
                </div>

                <div className="activity-card">
                  <h4>Water Intake</h4>
                  <div className="activity-value">{healthData.activities.water.today}L</div>
                  <div className="activity-goal">Goal: {healthData.activities.water.goal}L</div>
                  {renderProgressBar(healthData.activities.water.today, healthData.activities.water.goal, '#00bcd4')}
                </div>

                <div className="activity-card">
                  <h4>Exercise</h4>
                  <div className="activity-value">{healthData.activities.exercise.minutes}min</div>
                  <div className="activity-goal">Goal: {healthData.activities.exercise.goal}min</div>
                  {renderProgressBar(healthData.activities.exercise.minutes, healthData.activities.exercise.goal, '#ff9800')}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'trends' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="trends-dashboard"
            >
              <h3>Health Trends</h3>
              
              <div className="trends-section">
                <h4>Weekly Mood Tracking</h4>
                <div className="mood-timeline">
                  {healthData.trends.mood.map((mood, index) => (
                    <div key={index} className="mood-day">
                      <div className="mood-emoji">
                        {mood === 'Happy' ? '😊' : mood === 'Stressed' ? '😰' : mood === 'Calm' ? '😌' : mood === 'Energetic' ? '💪' : '😴'}
                      </div>
                      <span className="mood-label">{mood}</span>
                      <span className="day-label">Day {index + 1}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="trends-section">
                <h4>Energy & Stress Levels</h4>
                <div className="energy-stress-chart">
                  <div className="chart-labels">
                    <span>Energy</span>
                    <span>Stress</span>
                  </div>
                  <div className="chart-bars">
                    {healthData.trends.energy.map((energy, index) => (
                      <div key={index} className="chart-day">
                        <div 
                          className="energy-bar"
                          style={{ height: `${(energy / 10) * 100}%` }}
                          title={`Energy: ${energy}/10`}
                        ></div>
                        <div 
                          className="stress-bar"
                          style={{ height: `${(healthData.trends.stress[index] / 10) * 100}%` }}
                          title={`Stress: ${healthData.trends.stress[index]}/10`}
                        ></div>
                        <span className="day-number">{index + 1}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HealthAnalytics; 