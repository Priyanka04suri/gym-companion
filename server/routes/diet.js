import express from 'express';
import axios from 'axios';
import DietPlan from '../models/DietPlan.js';
import { auth } from '../middleware/auth.js';

const router = express.Router();

// POST /api/diet/generate - Generate diet plan via AI service (protected)
router.post('/generate', auth, async (req, res) => {
  try {
    const { date } = req.body;

    const response = await axios.post(`${process.env.AI_SERVICE_URL}/api/generate-diet`, {
      userId: req.user.userId,
      ...req.body
    });

    const dietData = response.data;

    const dietPlan = new DietPlan({
      userId: req.user.userId,
      date: date || new Date(),
      meals: dietData.meals
    });

    await dietPlan.save();

    res.status(201).json(dietPlan);
  } catch (err) {
    console.error('Generate diet error:', err);
    res.status(500).json({ error: 'Failed to generate diet plan.' });
  }
});

// GET /api/diet/today - Get today's diet plan (protected)
router.get('/today', auth, async (req, res) => {
  try {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const diet = await DietPlan.findOne({
      userId: req.user.userId,
      date: { $gte: today }
    }).populate('userId', 'name email');

    if (!diet) {
      return res.status(404).json({ error: 'No diet plan for today.' });
    }

    res.json(diet);
  } catch (err) {
    console.error('Get today diet error:', err);
    res.status(500).json({ error: 'Failed to fetch diet plan.' });
  }
});

export default router;
