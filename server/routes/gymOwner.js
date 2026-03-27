import express from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import GymOwner from '../models/GymOwner.js';
import User from '../models/User.js';
import Progress from '../models/Progress.js';
import { auth } from '../middleware/auth.js';

const router = express.Router();

// POST /api/gym-owner/register
router.post('/register', async (req, res) => {
  try {
    const { name, email, password, gymName } = req.body;

    const existingOwner = await GymOwner.findOne({ email });
    if (existingOwner) {
      return res.status(400).json({ error: 'Email already registered.' });
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    const gymOwner = new GymOwner({
      name,
      email,
      password: hashedPassword,
      gymName
    });

    await gymOwner.save();

    const token = jwt.sign({ gymOwnerId: gymOwner._id, email: gymOwner.email }, process.env.JWT_SECRET, { expiresIn: '7d' });

    res.status(201).json({ token, gymOwner: { id: gymOwner._id, name: gymOwner.name, email: gymOwner.email, gymName: gymOwner.gymName } });
  } catch (err) {
    console.error('Gym owner registration error:', err);
    res.status(500).json({ error: 'Failed to register gym owner.' });
  }
});

// POST /api/gym-owner/login
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    const gymOwner = await GymOwner.findOne({ email });
    if (!gymOwner) {
      return res.status(401).json({ error: 'Invalid credentials.' });
    }

    const isMatch = await bcrypt.compare(password, gymOwner.password);
    if (!isMatch) {
      return res.status(401).json({ error: 'Invalid credentials.' });
    }

    const token = jwt.sign({ gymOwnerId: gymOwner._id, email: gymOwner.email }, process.env.JWT_SECRET, { expiresIn: '7d' });

    res.json({ token, gymOwner: { id: gymOwner._id, name: gymOwner.name, email: gymOwner.email, gymName: gymOwner.gymName } });
  } catch (err) {
    console.error('Gym owner login error:', err);
    res.status(500).json({ error: 'Failed to login.' });
  }
});

// GET /api/gym-owner/members - Get all gym members (protected)
router.get('/members', auth, async (req, res) => {
  try {
    const gymOwner = await GymOwner.findById(req.user.gymOwnerId).populate('members');
    if (!gymOwner) {
      return res.status(404).json({ error: 'Gym owner not found.' });
    }

    res.json(gymOwner.members);
  } catch (err) {
    console.error('Get members error:', err);
    res.status(500).json({ error: 'Failed to fetch members.' });
  }
});

// GET /api/gym-owner/members/:id/progress - Get specific member's progress (protected)
router.get('/members/:id/progress', auth, async (req, res) => {
  try {
    const progress = await Progress.find({ userId: req.params.id })
      .sort({ date: 1 })
      .limit(90);

    res.json(progress);
  } catch (err) {
    console.error('Get member progress error:', err);
    res.status(500).json({ error: 'Failed to fetch member progress.' });
  }
});

// POST /api/gym-owner/announcement - Send announcement to all members (protected)
router.post('/announcement', auth, async (req, res) => {
  try {
    const { message } = req.body;

    const gymOwner = await GymOwner.findById(req.user.gymOwnerId);
    if (!gymOwner) {
      return res.status(404).json({ error: 'Gym owner not found.' });
    }

    // In a real app, this would send push notifications or emails
    // For now, we just acknowledge the announcement
    res.json({ message: 'Announcement sent to all members.', memberCount: gymOwner.members.length });
  } catch (err) {
    console.error('Send announcement error:', err);
    res.status(500).json({ error: 'Failed to send announcement.' });
  }
});

export default router;
