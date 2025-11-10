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
        if category not in self.workouts:
            raise ValueError("Invalid category. Must be one of: Warm-up, Workout, Cool-down")
        
        entry = {
            "exercise": exercise,
            "duration": duration,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.workouts[category].append(entry)

    def get_workouts(self):
        return self.workouts.copy()
    
    def get_all_sessions(self):
        """Get all sessions in a flat list format."""
        all_sessions = []
        for category, sessions in self.workouts.items():
            for session in sessions:
                session_copy = session.copy()
                session_copy['category'] = category
                all_sessions.append(session_copy)
        return all_sessions
    
    def get_summary(self):
        """Get workout summary with statistics."""
        total_time = 0
        session_count = 0
        summary = {}
        
        for category, sessions in self.workouts.items():
            category_time = sum(session['duration'] for session in sessions)
            total_time += category_time
            session_count += len(sessions)
            summary[category] = {
                'sessions': sessions,
                'count': len(sessions),
                'total_time': category_time
            }
        
        # Generate motivational message
        if total_time < 30:
            motivation = "Good start! Keep moving 💪"
        elif total_time < 60:
            motivation = "Nice effort! You're building consistency 🔥"
        else:
            motivation = "Excellent dedication! Keep up the great work 🏆"
        
        return {
            'categories': summary,
            'total_time': total_time,
            'session_count': session_count,
            'motivation': motivation
        }

manager = WorkoutManager()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        exercise = request.form.get('exercise')
        duration_str = request.form.get('duration')
        category = request.form.get('category', 'Workout')
        
        try:
            duration = int(duration_str)
            manager.add_workout(exercise, duration, category)
            flash(f"'{exercise}' added to {category} successfully!", 'success')
        except (ValueError, TypeError) as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))
    
    workouts = manager.get_workouts()
    return render_template('index.html', workouts=workouts, categories=list(workouts.keys()))

@app.route('/summary')
def summary():
    summary_data = manager.get_summary()
    return render_template('summary.html', summary=summary_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)