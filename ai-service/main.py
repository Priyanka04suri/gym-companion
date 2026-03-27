import os
import base64
import json
import numpy as np
import cv2
import mediapipe as mp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import anthropic

load_dotenv()

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5)


# Request/Response Models
class WorkoutRequest(BaseModel):
    goal: str
    experienceLevel: str
    dayOfWeek: int
    missedDays: int = 0
    previousExercises: Optional[List[str]] = []


class Exercise(BaseModel):
    name: str
    sets: int
    reps: str
    restSeconds: int
    muscleGroup: str
    difficulty: str


class WorkoutResponse(BaseModel):
    exercises: List[Exercise]


class DietRequest(BaseModel):
    goal: str
    weight: float
    dietPreference: str
    activityLevel: str


class MealMacros(BaseModel):
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    calories: float = 0


class Meal(BaseModel):
    foods: List[Dict[str, str]] = []
    macros: MealMacros = MealMacros()


class DietResponse(BaseModel):
    preWorkout: Meal = Meal()
    postWorkout: Meal = Meal()
    breakfast: Meal = Meal()
    lunch: Meal = Meal()
    dinner: Meal = Meal()
    totalCalories: int


class PoseRequest(BaseModel):
    image: str  # base64 encoded image


class PoseResponse(BaseModel):
    feedback: List[str]
    isCorrect: bool
    score: int


class RecommendationRequest(BaseModel):
    progressHistory: List[Dict[str, Any]]
    currentGoal: str
    workoutConsistency: float


class RecommendationResponse(BaseModel):
    adjustments: List[str]
    prediction: str


# Helper function to calculate angle between three points
def calculate_angle(a, b, c):
    """Calculate angle at point b formed by points a-b-c"""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    ba = a - b
    bc = c - b

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))

    return np.degrees(angle)


# POST /generate-workout
@app.post("/generate-workout", response_model=WorkoutResponse)
async def generate_workout(req: WorkoutRequest):
    prompt = f"""You are an expert fitness trainer. Create a workout plan based on these parameters:

- Goal: {req.goal}
- Experience Level: {req.experienceLevel}
- Day of Week: {req.dayOfWeek}
- Missed Days: {req.missedDays}
- Previous Exercises (avoid if possible): {req.previousExercises or 'None'}

Return ONLY valid JSON (no markdown, no explanation) in this exact format:
{{
  "exercises": [
    {{
      "name": "Exercise Name",
      "sets": 3,
      "reps": "10-12",
      "restSeconds": 60,
      "muscleGroup": "chest",
      "difficulty": "intermediate"
    }}
  ]
}}

Provide 6-8 exercises appropriate for the goal and experience level.
Muscle groups should be one of: chest, back, legs, shoulders, arms, core, cardio.
Difficulty should be one of: beginner, intermediate, advanced."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        workout_data = json.loads(response_text)

        return WorkoutResponse(exercises=workout_data["exercises"])
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


# POST /generate-diet
@app.post("/generate-diet", response_model=DietResponse)
async def generate_diet(req: DietRequest):
    veg_instruction = "STRICTLY vegetarian (no meat, fish, or eggs - dairy is ok)" if req.dietPreference == "veg" else "Non-vegetarian (meat and fish are allowed)"

    prompt = f"""You are an expert nutritionist. Create a full day meal plan based on these parameters:

- Goal: {req.goal}
- Weight: {req.weight}kg
- Diet Preference: {veg_instruction}
- Activity Level: {req.activityLevel}

Return ONLY valid JSON (no markdown, no explanation) in this exact format:
{{
  "preWorkout": {{
    "foods": [{{"name": "Food Name", "quantity": "100g"}}],
    "macros": {{"protein": 10, "carbs": 30, "fat": 5, "calories": 200}}
  }},
  "postWorkout": {{
    "foods": [{{"name": "Food Name", "quantity": "100g"}}],
    "macros": {{"protein": 25, "carbs": 40, "fat": 3, "calories": 300}}
  }},
  "breakfast": {{
    "foods": [{{"name": "Food Name", "quantity": "100g"}}],
    "macros": {{"protein": 20, "carbs": 50, "fat": 15, "calories": 400}}
  }},
  "lunch": {{
    "foods": [{{"name": "Food Name", "quantity": "100g"}}],
    "macros": {{"protein": 35, "carbs": 60, "fat": 20, "calories": 550}}
  }},
  "dinner": {{
    "foods": [{{"name": "Food Name", "quantity": "100g"}}],
    "macros": {{"protein": 30, "carbs": 45, "fat": 18, "calories": 450}}
  }},
  "totalCalories": 1900
}}

Ensure foods strictly respect the diet preference. Macros should be realistic values."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        # Extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        diet_data = json.loads(response_text)

        return DietResponse(
            preWorkout=Meal(**diet_data.get("preWorkout", {})),
            postWorkout=Meal(**diet_data.get("postWorkout", {})),
            breakfast=Meal(**diet_data.get("breakfast", {})),
            lunch=Meal(**diet_data.get("lunch", {})),
            dinner=Meal(**diet_data.get("dinner", {})),
            totalCalories=diet_data.get("totalCalories", 0)
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


# POST /analyze-pose
@app.post("/analyze-pose", response_model=PoseResponse)
async def analyze_pose(req: PoseRequest):
    try:
        # Decode base64 image
        image_data = base64.b64decode(req.image)
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return PoseResponse(feedback=["Invalid image"], isCorrect=False, score=0)

        # Process with MediaPipe Pose
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_image)

        if not results.pose_landmarks:
            return PoseResponse(feedback=["Stand in front of camera"], isCorrect=False, score=0)

        landmarks = results.pose_landmarks.landmark
        feedback = []
        score = 100

        # Get key landmarks
        def get_coords(landmark):
            return np.array([landmark.x, landmark.y, landmark.z])

        # Calculate joint angles
        try:
            # Left side
            left_shoulder = get_coords(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER])
            left_elbow = get_coords(landmarks[mp_pose.PoseLandmark.LEFT_ELBOW])
            left_wrist = get_coords(landmarks[mp_pose.PoseLandmark.LEFT_WRIST])
            left_hip = get_coords(landmarks[mp_pose.PoseLandmark.LEFT_HIP])
            left_knee = get_coords(landmarks[mp_pose.PoseLandmark.LEFT_KNEE])
            left_ankle = get_coords(landmarks[mp_pose.PoseLandmark.LEFT_ANKLE])

            # Right side
            right_shoulder = get_coords(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER])
            right_elbow = get_coords(landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW])
            right_wrist = get_coords(landmarks[mp_pose.PoseLandmark.RIGHT_WRIST])
            right_hip = get_coords(landmarks[mp_pose.PoseLandmark.RIGHT_HIP])
            right_knee = get_coords(landmarks[mp_pose.PoseLandmark.RIGHT_KNEE])
            right_ankle = get_coords(landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE])

            # Spine alignment (shoulders and hips)
            left_hip_y = left_hip[1]
            right_hip_y = right_hip[1]
            left_shoulder_y = left_shoulder[1]
            right_shoulder_y = right_shoulder[1]

            # Check shoulder alignment
            shoulder_diff = abs(left_shoulder_y - right_shoulder_y)
            if shoulder_diff > 0.05:
                feedback.append("Level your shoulders")
                score -= 10

            # Check hip alignment
            hip_diff = abs(left_hip_y - right_hip_y)
            if hip_diff > 0.05:
                feedback.append("Level your hips")
                score -= 10

            # Check knee angles (for squat assessment)
            left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
            right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)

            if left_knee_angle < 80 or right_knee_angle < 80:
                feedback.append("Straighten your legs slightly")
                score -= 15
            elif left_knee_angle > 170 or right_knee_angle > 170:
                feedback.append("Bend your knees slightly")
                score -= 15

            # Check elbow angle (for arm position)
            left_elbow_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
            right_elbow_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)

            if left_elbow_angle < 45 or right_elbow_angle < 45:
                feedback.append("Extend your arms more")
                score -= 10

            # Spine alignment check
            nose = get_coords(landmarks[mp_pose.PoseLandmark.NOSE])
            spine_mid = (left_shoulder + right_shoulder + left_hip + right_hip) / 4

            if abs(nose[0] - spine_mid[0]) > 0.15:
                feedback.append("Keep your spine aligned")
                score -= 15

        except (IndexError, KeyError, TypeError) as e:
            return PoseResponse(feedback=["Could not detect pose landmarks"], isCorrect=False, score=0)

        # Ensure score doesn't go below 0
        score = max(0, score)

        if not feedback:
            feedback.append("Good form!")

        return PoseResponse(
            feedback=feedback,
            isCorrect=len(feedback) == 1 and "Good" in feedback[0],
            score=score
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pose analysis error: {str(e)}")


# POST /smart-recommendations
@app.post("/smart-recommendations", response_model=RecommendationResponse)
async def smart_recommendations(req: RecommendationRequest):
    # Format progress history for prompt
    progress_summary = "\n".join([
        f"- {p.get('date', 'Unknown')}: {p.get('weight', 'N/A')}kg"
        for p in req.progressHistory[-10:]  # Last 10 entries
    ])

    prompt = f"""You are an expert fitness coach. Analyze this user's progress and provide recommendations.

**Progress History:**
{progress_summary}

**Current Goal:** {req.currentGoal}
**Workout Consistency:** {req.workoutConsistency}%

Analyze the trends and provide:
1. Specific adjustments to their diet and workout routine
2. A prediction for when they'll reach their goal at this rate

Return ONLY valid JSON (no markdown, no explanation) in this exact format:
{{
  "adjustments": [
    "Increase protein by 20g daily",
    "Add 1 set to compound lifts",
    "Reduce cardio by 10 minutes"
  ],
  "prediction": "At this rate, you will reach your goal in 6 weeks"
}}

Be specific and actionable with adjustments."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        # Extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        rec_data = json.loads(response_text)

        return RecommendationResponse(
            adjustments=rec_data.get("adjustments", []),
            prediction=rec_data.get("prediction", "")
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
