import mongoose from 'mongoose';

const macrosSchema = new mongoose.Schema({
  protein: { type: Number, default: 0 },
  carbs: { type: Number, default: 0 },
  fat: { type: Number, default: 0 },
  calories: { type: Number, default: 0 }
}, { _id: false });

const mealSchema = new mongoose.Schema({
  foods: [{
    name: String,
    quantity: String
  }],
  macros: { type: macrosSchema, default: () => ({}) }
}, { _id: false });

const dietPlanSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  date: {
    type: Date,
    required: true
  },
  meals: {
    preWorkout: { type: mealSchema, default: () => ({ foods: [] }) },
    postWorkout: { type: mealSchema, default: () => ({ foods: [] }) },
    breakfast: { type: mealSchema, default: () => ({ foods: [] }) },
    lunch: { type: mealSchema, default: () => ({ foods: [] }) },
    dinner: { type: mealSchema, default: () => ({ foods: [] }) }
  }
});

export default mongoose.model('DietPlan', dietPlanSchema);
