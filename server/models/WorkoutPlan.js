import mongoose from 'mongoose';

const exerciseSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true
  },
  sets: {
    type: Number,
    required: true
  },
  reps: {
    type: String,
    required: true
  },
  restSeconds: {
    type: Number,
    required: true
  },
  muscleGroup: {
    type: String,
    required: true
  },
  youtubeUrl: {
    type: String
  }
}, { _id: false });

const workoutPlanSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  date: {
    type: Date,
    required: true
  },
  exercises: [exerciseSchema],
  completed: {
    type: Boolean,
    default: false
  }
});

export default mongoose.model('WorkoutPlan', workoutPlanSchema);
