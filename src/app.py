from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')  # Use env variable in production

class WorkoutManager:
    def __init__(self):
        self.workouts = []

    def add_workout(self, workout, duration):
        if not workout or duration is None:
            raise ValueError("Workout and duration are required.")
        if not isinstance(duration, int):
            raise TypeError("Duration must be an integer.")
        self.workouts.append({"workout": workout, "duration": duration})

    def get_workouts(self):
        return self.workouts.copy()

manager = WorkoutManager()

@app.route('/', methods=['GET', 'POST'])
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

@app.route('/health')
def health_check():
    """Health check endpoint for load balancer"""
    return {'status': 'healthy', 'service': 'ace-fitness-app'}, 200

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html', workouts=manager.get_workouts()), 404

@app.errorhandler(500)
def internal_error(error):
    return {'error': 'Internal server error'}, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)