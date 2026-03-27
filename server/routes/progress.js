import express from 'express';
import Progress from '../models/Progress.js';
import { auth } from '../middleware/auth.js';

const router = express.Router();

// POST /api/progress/ - Log progress entry (protected)
router.post('/', auth, async (req, res) => {
  try {
    const { weight, bmi, workoutCompleted, notes } = req.body;

    const progress = new Progress({
      userId: req.user.userId,
      date: new Date(),
      weight,
      bmi,
      workoutCompleted,
      notes
    });

    await progress.save();

    res.status(201).json(progress);
  } catch (err) {
    console.error('Log progress error:', err);
    res.status(500).json({ error: 'Failed to log progress.' });
  }
});

// GET /api/progress/all - Get all progress entries for chart (protected)
router.get('/all', auth, async (req, res) => {
  try {
    const progress = await Progress.find({ userId: req.user.userId })
      .sort({ date: 1 })
      .limit(90);

    res.json(progress);
  } catch (err) {
    console.error('Get progress error:', err);
    res.status(500).json({ error: 'Failed to fetch progress.' });
  }
});

export default router;
