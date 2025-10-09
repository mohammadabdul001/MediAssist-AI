const express = require('express');
const router = express.Router();
const { PythonShell } = require('python-shell');
const path = require('path');
const auth = require('../middleware/auth');

// @route   POST /api/symptoms/analyze
// @desc    Analyze symptoms using ML
// @access  Private
router.post('/analyze', auth, async (req, res) => {
    try {
        const { symptoms, patientInfo } = req.body;
        
        if (!symptoms || !Array.isArray(symptoms) || symptoms.length === 0) {
            return res.status(400).json({ error: 'Please provide symptoms array' });
        }

        const options = {
            mode: 'text',
            pythonPath: 'python',
            pythonOptions: ['-u'],
            scriptPath: path.join(__dirname, '../ml_models'),
            args: [JSON.stringify(symptoms)]
        };

        PythonShell.run('symptom_analyzer.py', options, (err, results) => {
            if (err) {
                console.error('Python error:', err);
                return res.status(500).json({ error: 'Analysis failed' });
            }

            try {
                const result = JSON.parse(results[results.length - 1]);
                
                // Save analysis to database
                const Analysis = require('../models/Analysis');
                const analysis = new Analysis({
                    userId: req.user.id,
                    symptoms,
                    analysis: result,
                    timestamp: new Date()
                });
                
                analysis.save();

                res.json({
                    success: true,
                    analysis: result,
                    timestamp: new Date().toISOString()
                });
            } catch (parseError) {
                console.error('Parse error:', parseError);
                res.status(500).json({ error: 'Failed to parse analysis results' });
            }
        });

    } catch (error) {
        console.error('Symptom analysis error:', error);
        res.status(500).json({ error: 'Server error during analysis' });
    }
});

// @route   GET /api/symptoms/history
// @desc    Get user's symptom analysis history
// @access  Private
router.get('/history', auth, async (req, res) => {
    try {
        const Analysis = require('../models/Analysis');
        const history = await Analysis.find({ userId: req.user.id })
            .sort({ timestamp: -1 })
            .limit(50);
        
        res.json({
            success: true,
            history,
            count: history.length
        });
    } catch (error) {
        console.error('History error:', error);
        res.status(500).json({ error: 'Failed to fetch history' });
    }
});

// @route   GET /api/symptoms/recommendations
// @desc    Get AI recommendations based on symptoms
// @access  Private
router.post('/recommendations', auth, async (req, res) => {
    try {
        const { symptoms, severity } = req.body;
        
        const options = {
            mode: 'text',
            pythonPath: 'python',
            pythonOptions: ['-u'],
            scriptPath: path.join(__dirname, '../ml_models'),
            args: [JSON.stringify(symptoms), severity || 'low']
        };

        PythonShell.run('symptom_analyzer.py', options, (err, results) => {
            if (err) {
                console.error('Python error:', err);
                return res.status(500).json({ error: 'Recommendations failed' });
            }

            try {
                const result = JSON.parse(results[results.length - 1]);
                res.json({
                    success: true,
                    recommendations: result.get('recommendations', [])
                });
            } catch (parseError) {
                console.error('Parse error:', parseError);
                res.status(500).json({ error: 'Failed to parse recommendations' });
            }
        });

    } catch (error) {
        console.error('Recommendations error:', error);
        res.status(500).json({ error: 'Server error' });
    }
});

module.exports = router;
