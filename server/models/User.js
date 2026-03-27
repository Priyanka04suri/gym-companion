import mongoose from 'mongoose';

const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true
  },
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true
  },
  password: {
    type: String,
    required: true
  },
  height: {
    type: Number,
    min: 0
  },
  weight: {
    type: Number,
    min: 0
  },
  age: {
    type: Number,
    min: 0
  },
  goal: {
    type: String,
    enum: ['fatLoss', 'muscleGain', 'maintenance']
  },
  dietPreference: {
    type: String,
    enum: ['veg', 'nonVeg']
  },
  experienceLevel: {
    type: String,
    enum: ['beginner', 'intermediate', 'advanced']
  },
  gymOwnerId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'GymOwner'
  }
}, {
  timestamps: { createdAt: true, updatedAt: false }
});

export default mongoose.model('User', userSchema);
