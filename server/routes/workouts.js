import express from 'express';
import axios from 'axios';
import WorkoutPlan from '../models/WorkoutPlan.js';
import { auth } from '../middleware/auth.js';

const router = express.Router();

// POST /api/workouts/generate - Generate workout plan via AI service (protected)
router.post('/generate', auth, async (req, res) => {
  try {
    const { date } = req.body;

    const response = await axios.post(`${process.env.AI_SERVICE_URL}/api/generate-workout`, {
      userId: req.user.userId,
      ...req.body
    });

    const workoutData = response.data;

    const workoutPlan = new WorkoutPlan({
      userId: req.user.userId,
      date: date || new Date(),
      exercises: workoutData.exercises,
      completed: false
    });

    await workoutPlan.save();

    res.status(201).json(workoutPlan);
  } catch (err) {
    console.error('Generate workout error:', err);
    res.status(500).json({ error: 'Failed to generate workout plan.' });
  }
});

// GET /api/workouts/today - Get today's workout (protected)
router.get('/today', auth, async (req, res) => {
  try {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const workout = await WorkoutPlan.findOne({
      userId: req.user.userId,
      date: { $gte: today }
    }).populate('userId', 'name email');

    if (!workout) {
      return res.status(404).json({ error: 'No workout plan for today.' });
    }

    res.json(workout);
  } catch (err) {
    console.error('Get today workout error:', err);
    res.status(500).json({ error: 'Failed to fetch workout.' });
  }
});

// GET /api/workouts/history - Get workout history (protected)
router.get('/history', auth, async (req, res) => {
  try {
    const workouts = await WorkoutPlan.find({ userId: req.user.userId })
      .sort({ date: -1 })
      .limit(30);

    res.json(workouts);
  } catch (err) {
    console.error('Get workout history error:', err);
    res.status(500).json({ error: 'Failed to fetch workout history.' });
  }
});

export default router;
