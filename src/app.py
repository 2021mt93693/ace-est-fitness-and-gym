from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

class WorkoutManager:
    def __init__(self):
        self.workouts = {"Warm-up": [], "Workout": [], "Cool-down": []}

    def add_workout(self, exercise, duration, category="Workout"):
        if not exercise or duration is None:
            raise ValueError("Exercise and duration are required.")
        if not isinstance(duration, int):
            raise TypeError("Duration must be an integer.")
        if duration <= 0:
            raise ValueError("Duration must be positive.")
        if category not in self.workouts:
            raise ValueError("Invalid category.")
        
        entry = {
            "exercise": exercise,
            "duration": duration,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.workouts[category].append(entry)

    def get_workouts(self):
        return {category: sessions.copy() for category, sessions in self.workouts.items()}
    
    def get_all_workouts_flat(self):
        """Returns all workouts in a flat list for compatibility"""
        flat_list = []
        for category, sessions in self.workouts.items():
            for session in sessions:
                flat_list.append({
                    "workout": session["exercise"],
                    "duration": session["duration"],
                    "category": category,
                    "timestamp": session["timestamp"]
                })
        return flat_list
    
    def get_totals_by_category(self):
        """Returns total duration for each category"""
        return {category: sum(entry['duration'] for entry in sessions) 
                for category, sessions in self.workouts.items()}
    
    def get_total_time(self):
        """Returns total workout time across all categories"""
        return sum(sum(entry['duration'] for entry in sessions) 
                  for sessions in self.workouts.values())
    
    def has_workouts(self):
        """Check if any workouts have been logged"""
        return any(sessions for sessions in self.workouts.values())

manager = WorkoutManager()

# Workout plan data
WORKOUT_PLANS = {
    "Warm-up (5-10 min)": [
        "5 min light cardio (Jog/Cycle)",
        "Jumping Jacks (30 reps)",
        "Arm Circles (15 Fwd/Bwd)"
    ],
    "Strength Workout (45-60 min)": [
        "Push-ups (3 sets of 10-15)",
        "Squats (3 sets of 15-20)",
        "Plank (3 sets of 60 seconds)",
        "Lunges (3 sets of 10/leg)"
    ],
    "Cool-down (5 min)": [
        "Slow Walking",
        "Static Stretching (Hold 30s each)",
        "Deep Breathing Exercises"
    ]
}

# Diet guide data
DIET_PLANS = {
    "🎯 Weight Loss": [
        "Breakfast: Oatmeal with Berries",
        "Lunch: Grilled Chicken/Tofu Salad",
        "Dinner: Vegetable Soup with Lentils"
    ],
    "💪 Muscle Gain": [
        "Breakfast: 3 Egg Omelet, Spinach, Whole-wheat Toast",
        "Lunch: Chicken Breast, Quinoa, and Steamed Veggies",
        "Post-Workout: Protein Shake, Greek Yogurt"
    ],
    "🏃 Endurance Focus": [
        "Pre-Workout: Banana & Peanut Butter",
        "Lunch: Whole Grain Pasta with Light Sauce",
        "Dinner: Salmon & Avocado Salad"
    ]
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        exercise = request.form.get('exercise')
        duration_str = request.form.get('duration')
        category = request.form.get('category', 'Workout')
        
        try:
            duration = int(duration_str)
            manager.add_workout(exercise, duration, category)
            flash(f"'{exercise}' ({duration} min) added to {category} successfully!", 'success')
        except (ValueError, TypeError) as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))
    
    workouts = manager.get_workouts()
    return render_template('index.html', workouts=workouts)

@app.route('/workout-plan')
def workout_plan():
    return render_template('workout_plan.html', workout_plans=WORKOUT_PLANS)

@app.route('/diet-guide')
def diet_guide():
    return render_template('diet_guide.html', diet_plans=DIET_PLANS)

@app.route('/progress')
def progress():
    if not manager.has_workouts():
        flash('No workout data logged yet. Log a session to see your progress!', 'info')
    
    totals = manager.get_totals_by_category()
    total_time = manager.get_total_time()
    return render_template('progress.html', totals=totals, total_time=total_time)

@app.route('/summary')
def summary():
    workouts = manager.get_workouts()
    total_time = manager.get_total_time()
    return render_template('summary.html', workouts=workouts, total_time=total_time)

@app.route('/api/progress-data')
def progress_data():
    """API endpoint for chart data"""
    totals = manager.get_totals_by_category()
    # Filter out categories with 0 minutes
    filtered_totals = {k: v for k, v in totals.items() if v > 0}
    
    return jsonify({
        'categories': list(filtered_totals.keys()),
        'values': list(filtered_totals.values()),
        'total': manager.get_total_time()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)