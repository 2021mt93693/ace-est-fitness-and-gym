from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import copy

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

class WorkoutManager:
    def __init__(self):
        self.workouts = {"Warm-up": [], "Workout": [], "Cool-down": []}

    def add_workout(self, workout, duration, category="Workout"):
        if not workout or duration is None:
            raise ValueError("Workout and duration are required.")
        if not isinstance(duration, int):
            raise TypeError("Duration must be an integer.")
        if duration <= 0:
            raise ValueError("Duration must be positive.")
        if category not in self.workouts:
            raise ValueError("Invalid category.")
        
        entry = {
            "exercise": workout,
            "duration": duration,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": category
        }
        self.workouts[category].append(entry)

    def get_workouts(self):
        return copy.deepcopy(self.workouts)

    def get_all_workouts_flat(self):
        """Return all workouts as a flat list for backward compatibility"""
        all_workouts = []
        for category, exercises in self.workouts.items():
            for exercise in exercises:
                workout_entry = {
                    "workout": exercise["exercise"],
                    "duration": exercise["duration"],
                    "timestamp": exercise["timestamp"],
                    "category": category
                }
                all_workouts.append(workout_entry)
        return all_workouts

    def get_progress_data(self):
        """Get data for progress visualization"""
        totals = {}
        for category, sessions in self.workouts.items():
            totals[category] = sum(entry['duration'] for entry in sessions)
        return totals

    def get_workout_summary(self):
        """Get detailed workout summary"""
        summary = {}
        total_time = 0
        for category, sessions in self.workouts.items():
            category_time = sum(entry['duration'] for entry in sessions)
            summary[category] = {
                "sessions": sessions,
                "total_time": category_time,
                "count": len(sessions)
            }
            total_time += category_time
        summary["total_time"] = total_time
        return summary

manager = WorkoutManager()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        workout = request.form.get('workout')
        duration_str = request.form.get('duration')
        category = request.form.get('category', 'Workout')
        try:
            duration = int(duration_str)
            manager.add_workout(workout, duration, category)
            flash(f"'{workout}' added successfully to {category}!", 'success')
        except (ValueError, TypeError) as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))
    
    workouts = manager.get_all_workouts_flat()  # For backward compatibility
    categories = list(manager.get_workouts().keys())
    return render_template('index.html', workouts=workouts, categories=categories)

@app.route('/workout-plan')
def workout_plan():
    plan_data = {
        "Warm-up (5-10 min)": [
            "5 min light cardio (Jog/Cycle) to raise heart rate.",
            "Jumping Jacks (30 reps) for dynamic mobility.",
            "Arm Circles (15 Fwd/Bwd) to prepare shoulders."
        ],
        "Strength & Cardio (45-60 min)": [
            "Push-ups (3 sets of 10-15) - Upper body strength.",
            "Squats (3 sets of 15-20) - Lower body foundation.",
            "Plank (3 sets of 60 seconds) - Core stabilization.",
            "Lunges (3 sets of 10/leg) - Balance and leg development."
        ],
        "Cool-down (5 min)": [
            "Slow Walking - Bring heart rate down gradually.",
            "Static Stretching (Hold 30s each) - Focus on major muscle groups.",
            "Deep Breathing Exercises - Aid recovery and relaxation."
        ]
    }
    return render_template('workout_plan.html', plan_data=plan_data)

@app.route('/diet-guide')
def diet_guide():
    diet_plans = {
        "🎯 Weight Loss Focus (Calorie Deficit)": [
            "Breakfast: Oatmeal with Berries (High Fiber).",
            "Lunch: Grilled Chicken/Tofu Salad (Lean Protein).",
            "Dinner: Vegetable Soup with Lentils (Low Calorie, High Volume)."
        ],
        "💪 Muscle Gain Focus (High Protein)": [
            "Breakfast: 3 Egg Omelet, Spinach, Whole-wheat Toast (Protein/Carb combo).",
            "Lunch: Chicken Breast, Quinoa, and Steamed Veggies (Balanced Meal).",
            "Post-Workout: Protein Shake & Greek Yogurt (Immediate Recovery)."
        ],
        "🏃 Endurance Focus (Complex Carbs)": [
            "Pre-Workout: Banana & Peanut Butter (Quick Energy).",
            "Lunch: Whole Grain Pasta with Light Sauce (Sustainable Carbs).",
            "Dinner: Salmon & Avocado Salad (Omega-3s and Healthy Fats)."
        ]
    }
    return render_template('diet_guide.html', diet_plans=diet_plans)

@app.route('/progress')
def progress():
    progress_data = manager.get_progress_data()
    workout_summary = manager.get_workout_summary()
    return render_template('progress.html', 
                         progress_data=progress_data, 
                         workout_summary=workout_summary)

@app.route('/api/progress-data')
def api_progress_data():
    """API endpoint for chart data"""
    return jsonify(manager.get_progress_data())

@app.route('/workout-summary')
def workout_summary():
    summary = manager.get_workout_summary()
    return render_template('workout_summary.html', summary=summary)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)