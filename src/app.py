from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)