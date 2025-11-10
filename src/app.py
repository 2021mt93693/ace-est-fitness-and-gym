from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

class WorkoutManager:
    def __init__(self):
        self.workouts = {"Warm-up": [], "Workout": [], "Cool-down": []}
        
    def add_workout(self, category, workout, duration):
        if not workout or duration is None:
            raise ValueError("Workout and duration are required.")
        if not isinstance(duration, int):
            raise TypeError("Duration must be an integer.")
        if category not in self.workouts:
            raise ValueError("Invalid category.")
        
        entry = {
            "exercise": workout,
            "duration": duration,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.workouts[category].append(entry)

    def get_workouts(self):
        return self.workouts.copy()
    
    def get_total_time(self):
        total = 0
        for category, sessions in self.workouts.items():
            for session in sessions:
                total += session['duration']
        return total
    
    def get_summary(self):
        total_time = self.get_total_time()
        if total_time < 30:
            motivation = "Good start! Keep moving 💪"
        elif total_time < 60:
            motivation = "Nice effort! You're building consistency 🔥"
        else:
            motivation = "Excellent dedication! Keep up the great work 🏆"
        
        return {
            'workouts': self.workouts,
            'total_time': total_time,
            'motivation': motivation
        }

manager = WorkoutManager()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        category = request.form.get('category')
        workout = request.form.get('workout')
        duration_str = request.form.get('duration')
        try:
            duration = int(duration_str)
            manager.add_workout(category, workout, duration)
            flash(f"'{workout}' added to {category} successfully!", 'success')
        except (ValueError, TypeError) as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))
    
    workouts = manager.get_workouts()
    return render_template('index.html', workouts=workouts)

@app.route('/summary')
def summary():
    summary_data = manager.get_summary()
    return render_template('summary.html', summary=summary_data)

@app.route('/workout-chart')
def workout_chart():
    chart_data = {
        "Warm-up": ["5 min Jog", "Jumping Jacks", "Arm Circles", "Leg Swings", "Dynamic Stretching"],
        "Workout": ["Push-ups", "Squats", "Plank", "Lunges", "Burpees", "Crunches"],
        "Cool-down": ["Slow Walking", "Static Stretching", "Deep Breathing", "Yoga Poses"]
    }
    return render_template('workout_chart.html', chart_data=chart_data)

@app.route('/diet-chart')
def diet_chart():
    diet_plans = {
        "Weight Loss": ["Oatmeal with Fruits", "Grilled Chicken Salad", "Vegetable Soup", "Brown Rice & Stir-fry Veggies"],
        "Muscle Gain": ["Egg Omelet", "Chicken Breast", "Quinoa & Beans", "Protein Shake", "Greek Yogurt with Nuts"],
        "Endurance": ["Banana & Peanut Butter", "Whole Grain Pasta", "Sweet Potatoes", "Salmon & Avocado", "Trail Mix"]
    }
    return render_template('diet_chart.html', diet_plans=diet_plans)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)