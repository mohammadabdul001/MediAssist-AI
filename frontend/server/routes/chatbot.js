const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');

// @route   POST /api/chatbot/message
// @desc    Handle chatbot messages using AI
// @access  Private
router.post('/message', auth, async (req, res) => {
    try {
        const { message, context } = req.body;
        
        // Simple AI chatbot response (will be enhanced with actual AI)
        const responses = {
            'hello': 'Hello! How can I help you with your health today?',
            'symptoms': 'I can help you analyze your symptoms. Please describe what you\'re experiencing.',
            'medication': 'I can help you track your medications. What would you like to know?',
            'appointment': 'You can schedule appointments through the appointment section.',
            'emergency': 'For emergencies, please call 911 or go to the nearest emergency room.',
            'thank you': 'You\'re welcome! Is there anything else I can help you with?'
        };

        // Simple keyword matching for demo
        let response = 'I\'m here to help! Please let me know what you need assistance with.';

        for (const [keyword, reply] of Object.entries(responses)) {
            if (message.toLowerCase().includes(keyword)) {
                response = reply;
                break;
            }
        }

        res.json({
            success: true,
            response,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Chatbot error:', error);
        res.status(500).json({ error: 'Chatbot service unavailable' });
    }
});

// @route   GET /api/chatbot/suggestions
// @desc    Get AI chatbot suggestions
// @access  Private
router.get('/suggestions', auth, async (req, res) => {
    try {
        const suggestions = [
            'How can I help you with your symptoms?',
            'Would you like to schedule an appointment?',
            'I can help you track your medications',
            'Let me know if you need emergency assistance',
            'I can provide health recommendations'
        ];

        res.json({
            success: true,
            suggestions,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Suggestions error:', error);
        res.status(500).json({ error: 'Suggestions unavailable' });
    }
});

module.exports = router;
