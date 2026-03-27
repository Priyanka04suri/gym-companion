import express from 'express';
import User from '../models/User.js';
import { auth } from '../middleware/auth.js';

const router = express.Router();

// GET /api/users/me - Get current user profile (protected)
router.get('/me', auth, async (req, res) => {
  try {
    const user = await User.findById(req.user.userId).select('-password');
    if (!user) {
      return res.status(404).json({ error: 'User not found.' });
    }
    res.json(user);
  } catch (err) {
    console.error('Get user error:', err);
    res.status(500).json({ error: 'Failed to fetch user.' });
  }
});

// PUT /api/users/me - Update user profile (protected)
router.put('/me', auth, async (req, res) => {
  try {
    const { name, height, weight, age, goal, dietPreference, experienceLevel } = req.body;

    const user = await User.findByIdAndUpdate(
      req.user.userId,
      { name, height, weight, age, goal, dietPreference, experienceLevel },
      { new: true, runValidators: true }
    ).select('-password');

    if (!user) {
      return res.status(404).json({ error: 'User not found.' });
    }

    res.json(user);
  } catch (err) {
    console.error('Update user error:', err);
    res.status(500).json({ error: 'Failed to update user.' });
  }
});

export default router;
