import mongoose from 'mongoose';

const progressSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  date: {
    type: Date,
    required: true
  },
  weight: {
    type: Number,
    required: true
  },
  bmi: {
    type: Number
  },
  workoutCompleted: {
    type: Boolean,
    default: false
  },
  notes: {
    type: String
  }
});

export default mongoose.model('Progress', progressSchema);
