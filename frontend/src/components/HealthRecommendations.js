import React, { useState, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { motion } from 'framer-motion';

const HealthRecommendations = () => {
  const { t } = useAppContext();
  const [activeTab, setActiveTab] = useState('daily');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const recommendations = {
    daily: [
      {
        id: 1,
        title: 'Stay Hydrated',
        description: 'Drink 8-10 glasses of water daily to maintain optimal hydration',
        category: 'nutrition',
        priority: 'high',
        icon: '💧',
        tips: [
          'Start your day with a glass of water',
          'Keep a water bottle with you',
          'Set hydration reminders'
        ],
        progress: 75
      },
      {
        id: 2,
        title: 'Take Regular Breaks',
        description: 'Take 5-minute breaks every hour to reduce eye strain and improve focus',
        category: 'wellness',
        priority: 'medium',
        icon: '⏰',
        tips: [
          'Use the 20-20-20 rule (look 20 feet away for 20 seconds every 20 minutes)',
          'Stand up and stretch',
          'Practice deep breathing exercises'
        ],
        progress: 60
      },
      {
        id: 3,
        title: 'Mindful Eating',
        description: 'Practice mindful eating to improve digestion and prevent overeating',
        category: 'nutrition',
        priority: 'medium',
        icon: '🍽️',
        tips: [
          'Eat slowly and savor each bite',
          'Avoid distractions while eating',
          'Listen to your body\'s hunger cues'
        ],
        progress: 45
      }
    ],
    weekly: [
      {
        id: 4,
        title: 'Exercise Routine',
        description: 'Aim for 150 minutes of moderate exercise per week',
        category: 'fitness',
        priority: 'high',
        icon: '🏃‍♂️',
        tips: [
          'Mix cardio and strength training',
          'Find activities you enjoy',
          'Start with 30 minutes, 5 days a week'
        ],
        progress: 80
      },
      {
        id: 5,
        title: 'Sleep Schedule',
        description: 'Maintain a consistent sleep schedule for better rest',
        category: 'wellness',
        priority: 'high',
        icon: '😴',
        tips: [
          'Go to bed and wake up at the same time',
          'Create a relaxing bedtime routine',
          'Avoid screens 1 hour before bed'
        ],
        progress: 70
      },
      {
        id: 6,
        title: 'Social Connection',
        description: 'Spend quality time with friends and family',
        category: 'mental-health',
        priority: 'medium',
        icon: '👥',
        tips: [
          'Schedule regular meetups',
          'Try new activities together',
          'Practice active listening'
        ],
        progress: 65
      }
    ],
    monthly: [
      {
        id: 7,
        title: 'Health Check-up',
        description: 'Schedule your annual health check-up and screenings',
        category: 'preventive',
        priority: 'high',
        icon: '🏥',
        tips: [
          'Book appointments in advance',
          'Prepare a list of questions',
          'Bring your medical history'
        ],
        progress: 90
      },
      {
        id: 8,
        title: 'Learn New Skills',
        description: 'Challenge your mind with new activities or hobbies',
        category: 'mental-health',
        priority: 'medium',
        icon: '🧠',
        tips: [
          'Take an online course',
          'Learn a new language',
          'Try a new hobby or craft'
        ],
        progress: 40
      }
    ]
  };

  const categories = [
    { value: 'all', label: 'All Categories', icon: '📋' },
    { value: 'nutrition', label: 'Nutrition', icon: '🥗' },
    { value: 'fitness', label: 'Fitness', icon: '💪' },
    { value: 'wellness', label: 'Wellness', icon: '🧘‍♀️' },
    { value: 'mental-health', label: 'Mental Health', icon: '🧠' },
    { value: 'preventive', label: 'Preventive Care', icon: '🛡️' }
  ];

  const priorityColors = {
    high: '#f44336',
    medium: '#ff9800',
    low: '#4caf50'
  };

  const getFilteredRecommendations = () => {
    const allRecs = [...recommendations.daily, ...recommendations.weekly, ...recommendations.monthly];
    if (selectedCategory === 'all') return allRecs;
    return allRecs.filter(rec => rec.category === selectedCategory);
  };

  const markAsCompleted = (id) => {
    // Implementation for marking recommendations as completed
    console.log('Marked as completed:', id);
  };

  const renderProgressBar = (progress) => (
    <div className="progress-container">
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ 
            width: `${progress}%`,
            backgroundColor: progress >= 80 ? '#4caf50' : progress >= 60 ? '#ff9800' : '#f44336'
          }}
        ></div>
      </div>
      <span className="progress-text">{progress}%</span>
    </div>
  );

  return (
    <div className="health-recommendations">
      <div className="recommendations-container">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="recommendations-title"
        >
          💡 Personalized Health Recommendations
        </motion.h2>

        <div className="recommendations-header">
          <div className="category-filter">
            <label>Filter by Category:</label>
            <select 
              value={selectedCategory} 
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              {categories.map(category => (
                <option key={category.value} value={category.value}>
                  {category.icon} {category.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="recommendations-tabs">
          <button
            className={`tab ${activeTab === 'daily' ? 'active' : ''}`}
            onClick={() => setActiveTab('daily')}
          >
            Daily Tips
          </button>
          <button
            className={`tab ${activeTab === 'weekly' ? 'active' : ''}`}
            onClick={() => setActiveTab('weekly')}
          >
            Weekly Goals
          </button>
          <button
            className={`tab ${activeTab === 'monthly' ? 'active' : ''}`}
            onClick={() => setActiveTab('monthly')}
          >
            Monthly Check-ins
          </button>
        </div>

        <div className="recommendations-content">
          <div className="recommendations-grid">
            {getFilteredRecommendations().map(recommendation => (
              <motion.div
                key={recommendation.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="recommendation-card"
              >
                <div className="recommendation-header">
                  <div className="recommendation-icon">{recommendation.icon}</div>
                  <div className="recommendation-info">
                    <h4>{recommendation.title}</h4>
                    <p>{recommendation.description}</p>
                  </div>
                  <div className="priority-badge" style={{ backgroundColor: priorityColors[recommendation.priority] }}>
                    {recommendation.priority}
                  </div>
                </div>

                <div className="recommendation-progress">
                  <label>Progress</label>
                  {renderProgressBar(recommendation.progress)}
                </div>

                <div className="recommendation-tips">
                  <h5>💡 Tips:</h5>
                  <ul>
                    {recommendation.tips.map((tip, index) => (
                      <li key={index}>{tip}</li>
                    ))}
                  </ul>
                </div>

                <div className="recommendation-actions">
                  <button 
                    onClick={() => markAsCompleted(recommendation.id)}
                    className="btn-primary"
                  >
                    ✅ Mark Complete
                  </button>
                  <button className="btn-secondary">📝 Add Note</button>
                  <button className="btn-secondary">⏰ Remind Later</button>
                </div>
              </motion.div>
            ))}
          </div>

          {getFilteredRecommendations().length === 0 && (
            <div className="no-recommendations">
              <p>No recommendations found for the selected category.</p>
            </div>
          )}
        </div>

        <div className="insights-section">
          <h3>AI Health Insights</h3>
          <div className="insights-grid">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="insight-card"
            >
              <h4>🎯 Personalized Goals</h4>
              <p>Based on your health data, we recommend focusing on:</p>
              <ul>
                <li>Increasing daily water intake</li>
                <li>Adding more physical activity</li>
                <li>Improving sleep quality</li>
              </ul>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="insight-card"
            >
              <h4>📈 Progress Trends</h4>
              <p>Your health trends show:</p>
              <ul>
                <li>✅ Consistent medication adherence</li>
                <li>📊 Improving blood pressure readings</li>
                <li>⚠️ Need to increase exercise frequency</li>
              </ul>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="insight-card"
            >
              <h4>🔮 Predictive Insights</h4>
              <p>AI analysis suggests:</p>
              <ul>
                <li>Maintain current diet for optimal results</li>
                <li>Consider stress management techniques</li>
                <li>Schedule preventive screenings</li>
              </ul>
            </motion.div>
          </div>
        </div>

        <div className="customization-section">
          <h3>Customize Your Recommendations</h3>
          <div className="customization-options">
            <div className="option-group">
              <label>
                <input type="checkbox" defaultChecked /> Receive daily health tips
              </label>
              <label>
                <input type="checkbox" defaultChecked /> Weekly progress summaries
              </label>
              <label>
                <input type="checkbox" /> Monthly health reports
              </label>
            </div>
            
            <div className="option-group">
              <label>Notification Frequency:</label>
              <select defaultValue="daily">
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HealthRecommendations; 