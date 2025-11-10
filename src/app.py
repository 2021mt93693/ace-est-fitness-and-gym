from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

class WorkoutManager:
    def __init__(self):
        # Initialize workout dictionary with categories
        self.workouts = {"Warm-up": [], "Workout": [], "Cool-down": []}
        
        # Predefined exercise suggestions
        self.exercise_suggestions = {
            "Warm-up": ["5 min Jog", "Jumping Jacks", "Arm Circles", "Leg Swings", "Dynamic Stretching"],
            "Workout": ["Push-ups", "Squats", "Plank", "Lunges", "Burpees", "Crunches"],
            "Cool-down": ["Slow Walking", "Static Stretching", "Deep Breathing", "Yoga Poses"]
        }
        
        # Diet plans
        self.diet_plans = {
            "Weight Loss": ["Oatmeal with Fruits", "Grilled Chicken Salad", "Vegetable Soup", "Brown Rice & Veggies"],
            "Muscle Gain": ["Egg Omelet", "Chicken Breast", "Quinoa & Beans", "Protein Shake", "Greek Yogurt with Nuts"],
            "Endurance": ["Banana & Peanut Butter", "Whole Grain Pasta", "Sweet Potatoes", "Salmon & Avocado", "Trail Mix"]
        }

    def add_workout(self, exercise, duration, category="Workout"):
        if not exercise or duration is None:
            raise ValueError("Exercise and duration are required.")
        if not isinstance(duration, int):
            raise TypeError("Duration must be an integer.")
        if category not in self.workouts:
            raise ValueError("Invalid category. Must be one of: Warm-up, Workout, Cool-down")
        
        entry = {
            "exercise": exercise,
            "duration": duration,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": category
        }
        self.workouts[category].append(entry)

    def get_workouts(self):
        # Return all workouts in a flat list for compatibility
        all_workouts = []
        for category, sessions in self.workouts.items():
            all_workouts.extend(sessions)
        return all_workouts.copy()
    
    def get_workouts_by_category(self):
        return {category: sessions.copy() for category, sessions in self.workouts.items()}
    
    def get_total_time(self):
        total = 0
        for category, sessions in self.workouts.items():
            total += sum(entry['duration'] for entry in sessions)
        return total
    
    def get_category_totals(self):
        return {category: sum(entry['duration'] for entry in sessions) 
                for category, sessions in self.workouts.items()}
    
    def get_exercise_suggestions(self, category="Workout"):
        return self.exercise_suggestions.get(category, [])
    
    def get_diet_plans(self):
        import copy
        return copy.deepcopy(self.diet_plans)

manager = WorkoutManager()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/log', methods=['GET', 'POST'])
def log_workout():
    if request.method == 'POST':
        exercise = request.form.get('exercise')
        duration_str = request.form.get('duration')
        category = request.form.get('category', 'Workout')
        try:
            duration = int(duration_str)
            manager.add_workout(exercise, duration, category)
            flash(f"'{exercise}' added successfully to {category}!", 'success')
        except (ValueError, TypeError) as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('log_workout'))
    
    categories = list(manager.workouts.keys())
    suggestions = {cat: manager.get_exercise_suggestions(cat) for cat in categories}
    workouts_by_category = manager.get_workouts_by_category()
    return render_template('log_workout.html', 
                         categories=categories, 
                         suggestions=suggestions,
                         workouts_by_category=workouts_by_category)

@app.route('/summary')
def view_summary():
    workouts_by_category = manager.get_workouts_by_category()
    total_time = manager.get_total_time()
    category_totals = manager.get_category_totals()
    return render_template('summary.html', 
                         workouts_by_category=workouts_by_category,
                         total_time=total_time,
                         category_totals=category_totals)

@app.route('/workout-chart')
def workout_chart():
    suggestions = {cat: manager.get_exercise_suggestions(cat) 
                  for cat in manager.workouts.keys()}
    return render_template('workout_chart.html', suggestions=suggestions)

@app.route('/diet-chart')
def diet_chart():
    diet_plans = manager.get_diet_plans()
    return render_template('diet_chart.html', diet_plans=diet_plans)

@app.route('/progress')
def progress_tracker():
    category_totals = manager.get_category_totals()
    return render_template('progress.html', category_totals=category_totals)

@app.route('/api/progress-data')
def progress_data():
    """API endpoint for chart data"""
    category_totals = manager.get_category_totals()
    return jsonify(category_totals)

# Keep the original index route for backward compatibility
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        workout = request.form.get('workout')
        duration_str = request.form.get('duration')
        try:
            duration = int(duration_str)
            manager.add_workout(workout, duration)
            flash(f"'{workout}' added successfully!", 'success')
        except (ValueError, TypeError):
            flash('Please enter a valid workout and duration (number).', 'danger')
        return redirect(url_for('index'))
    workouts = manager.get_workouts()
    return render_template('index.html', workouts=workouts)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)