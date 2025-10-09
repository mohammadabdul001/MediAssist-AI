const express = require('express');
const router = express.Router();
const { PythonShell } = require('python-shell');
const path = require('path');
const auth = require('../middleware/auth');

// @route   POST /api/medications/track
// @desc    Track medication adherence using AI
// @access  Private
router.post('/track', auth, async (req, res) => {
    try {
        const { medications, patient_data } = req.body;
        
        if (!medications || !Array.isArray(medications) || medications.length === 0) {
            return res.status(400).json({ error: 'Please provide medications array' });
        }

        const options = {
            mode: 'text',
            pythonPath: 'python',
            pythonOptions: ['-u'],
            scriptPath: path.join(__dirname, '../ml_models'),
            args: [JSON.stringify(medications), JSON.stringify(patient_data)]
        };

        PythonShell.run('medication_ai.py', options, (err, results) => {
            if (err) {
                console.error('Python error:', err);
                return res.status(500).json({ error: 'Tracking failed' });
            }

            try {
                const result = JSON.parse(results[results.length - 1]);
                
                // Save tracking data to database
                const MedicationTracker = require('../models/MedicationTracker');
                const tracking = new MedicationTracker({
                    userId: req.user.id,
                    medications,
                    patient_data,
                    analysis: result,
                    timestamp: new Date()
                });
                
                tracking.save();

                res.json({
                    success: true,
                    analysis: result,
                    timestamp: new Date().toISOString()
                });
            } catch (parseError) {
                console.error('Parse error:', parseError);
                res.status(500).json({ error: 'Failed to parse tracking results' });
            }
        });

    } catch (error) {
        console.error('Medication tracking error:', error);
        res.status(500).json({ error: 'Server error during tracking' });
    }
});

// @route   GET /api/medications/schedule
// @desc    Get personalized medication schedule
// @access  Private
router.get('/schedule', auth, async (req, res) => {
    try {
        const MedicationTracker = require('../models/MedicationTracker');
        const schedule = await MedicationTracker.find({ userId: req.user.id })
            .sort({ timestamp: -1 })
            .limit(10);
        
        res.json({
            success: true,
            schedule,
            count: schedule.length
        });
    } catch (error) {
        console.error('Schedule error:', error);
        res.status(500).json({ error: 'Failed to fetch schedule' });
    }
});

// @route   POST /api/medications/reminders
// @desc    Generate personalized medication reminders
// @access  Private
router.post('/reminders', auth, async (req, res) => {
    try {
        const { medications, adherence_rate } = req.body;
        
        const options = {
            mode: 'text',
            pythonPath: 'python',
            pythonOptions: ['-u'],
            scriptPath: path.join(__dirname, '../ml_models'),
            args: [JSON.stringify(medications), str(adherence_rate)]
        };

        PythonShell.run('medication_ai.py', options, (err, results) => {
            if (err) {
                console.error('Python error:', err);
                return res.status(500).json({ error: 'Reminders failed' });
            }

            try {
                const reminders = JSON.parse(results[results.length - 1]);
                res.json({
                    success: true,
                    reminders,
                    timestamp: new Date().toISOString()
                });
            } catch (parseError) {
                console.error('Parse error:', parseError);
                res.status(500).json({ error: 'Failed to parse reminders' });
            }
        });

    } catch (error) {
        console.error('Reminders error:', error);
        res.status(500).json({ error: 'Server error' });
    }
});

// @route   GET /api/medications/stats
// @desc    Get medication tracking statistics
// @access  Private
router.get('/stats', auth, async (req, res) => {
    try {
        const MedicationTracker = require('../models/MedicationTracker');
        const stats = await MedicationTracker.aggregate([
            { $match: { userId: req.user.id } },
            {
                $group: {
                    _id: null,
                    totalMedications: { $sum: 1 },
                    averageAdherence: { $avg: '$analysis.adherence_rate' },
                    totalTaken: { $sum: '$analysis.taken_today' },
                    totalMissed: { $sum: '$analysis.missed_today' }
                }
            }
        ]);

        res.json({
            success: true,
            stats: stats[0] || {
                totalMedications: 0,
                averageAdherence: 0,
                totalTaken: 0,
                totalMissed: 0
            }
        });
    } catch (error) {
        console.error('Stats error:', error);
        res.status(500).json({ error: 'Failed to fetch stats' });
    }
});

module.exports = router;
