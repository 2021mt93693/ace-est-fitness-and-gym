from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web
import base64
import io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors as rl_colors
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

# ---------- MET Values for Exercises ----------
MET_VALUES = {
    "Warm-up": 3,
    "Workout": 6,
    "Cool-down": 2.5
}

class FitnessTracker:
    def __init__(self):
        # User info
        self.user_info = {}
        # Workouts by category
        self.workouts = {"Warm-up": [], "Workout": [], "Cool-down": []}
        # Daily workouts tracking
        self.daily_workouts = {}
    
    def save_user_info(self, name, regn_id, age, gender, height_cm, weight_kg):
        """Save user information and calculate BMI and BMR"""
        if not all([name, regn_id, age, gender, height_cm, weight_kg]):
            raise ValueError("All user info fields are required.")
        
        try:
            age = int(age)
            height_cm = float(height_cm)
            weight_kg = float(weight_kg)
            gender = gender.upper()
            
            if gender not in ["M", "F"]:
                raise ValueError("Gender must be M or F")
            
            # Calculate BMI
            bmi = weight_kg / ((height_cm/100)**2)
            
            # Calculate BMR using Mifflin-St Jeor Equation
            if gender == "M":
                bmr = 10*weight_kg + 6.25*height_cm - 5*age + 5
            else:
                bmr = 10*weight_kg + 6.25*height_cm - 5*age - 161
                
            self.user_info = {
                "name": name,
                "regn_id": regn_id,
                "age": age,
                "gender": gender,
                "height": height_cm,
                "weight": weight_kg,
                "bmi": bmi,
                "bmr": bmr,
                "weekly_cal_goal": 2000
            }
            return True
            
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid input: {e}")
    
    def add_workout(self, category, exercise, duration):
        """Add a workout session with calorie calculation"""
        if not exercise or duration is None:
            raise ValueError("Exercise and duration are required.")
        if not isinstance(duration, int) or duration <= 0:
            raise ValueError("Duration must be a positive integer.")
        if category not in self.workouts:
            raise ValueError("Invalid category. Must be Warm-up, Workout, or Cool-down.")
        
        # Calculate calories burned
        weight = self.user_info.get("weight", 70)  # Default weight if user info not set
        met = MET_VALUES.get(category, 5)
        calories = (met * 3.5 * weight / 200) * duration
        
        entry = {
            "exercise": exercise,
            "duration": duration,
            "calories": calories,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.workouts[category].append(entry)
        
        # Track daily workouts
        today_iso = date.today().isoformat()
        if today_iso not in self.daily_workouts:
            self.daily_workouts[today_iso] = {"Warm-up": [], "Workout": [], "Cool-down": []}
        self.daily_workouts[today_iso][category].append(entry)
        
        return entry

    def get_workouts(self):
        """Get all workouts"""
        return self.workouts.copy()
    
    def get_workout_summary(self):
        """Get summary statistics"""
        total_time = 0
        total_calories = 0
        category_totals = {}
        
        for category, sessions in self.workouts.items():
            cat_time = sum(entry['duration'] for entry in sessions)
            cat_calories = sum(entry['calories'] for entry in sessions)
            category_totals[category] = {
                'time': cat_time,
                'calories': cat_calories,
                'sessions': len(sessions)
            }
            total_time += cat_time
            total_calories += cat_calories
        
        return {
            'total_time': total_time,
            'total_calories': total_calories,
            'category_totals': category_totals
        }
    
    def get_user_info(self):
        """Get user information"""
        return self.user_info.copy()

# Global fitness tracker instance
tracker = FitnessTracker()

@app.route('/')
def index():
    """Main dashboard"""
    workouts = tracker.get_workouts()
    user_info = tracker.get_user_info()
    summary = tracker.get_workout_summary()
    return render_template('index.html', 
                         workouts=workouts, 
                         user_info=user_info, 
                         summary=summary)

@app.route('/save_user_info', methods=['POST'])
def save_user_info():
    """Save user information"""
    try:
        name = request.form.get('name', '').strip()
        regn_id = request.form.get('regn_id', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        height = request.form.get('height', '').strip()
        weight = request.form.get('weight', '').strip()
        
        tracker.save_user_info(name, regn_id, age, gender, height, weight)
        flash(f'User info saved! BMI: {tracker.user_info["bmi"]:.1f}, BMR: {tracker.user_info["bmr"]:.0f} kcal/day', 'success')
        
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash(f'Error saving user info: {e}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/add_workout', methods=['POST'])
def add_workout():
    """Add a workout session"""
    try:
        category = request.form.get('category')
        exercise = request.form.get('exercise', '').strip()
        duration_str = request.form.get('duration', '').strip()
        
        if not exercise or not duration_str:
            raise ValueError("Please enter both exercise and duration.")
        
        duration = int(duration_str)
        entry = tracker.add_workout(category, exercise, duration)
        flash(f"Added {exercise} ({duration} min) to {category}! Burned ~{entry['calories']:.1f} calories 💪", 'success')
        
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash(f'Error adding workout: {e}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/chart')
def chart():
    """Generate progress charts"""
    summary = tracker.get_workout_summary()
    category_totals = summary['category_totals']
    
    # Create charts
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Bar chart
    categories = list(category_totals.keys())
    times = [category_totals[cat]['time'] for cat in categories]
    colors = ['#2196F3', '#4CAF50', '#FFC107']  # Blue, Green, Yellow
    
    if sum(times) > 0:
        ax1.bar(categories, times, color=colors)
        ax1.set_title('Total Minutes per Category')
        ax1.set_ylabel('Minutes')
        ax1.grid(axis='y', alpha=0.3)
        
        # Pie chart
        pie_labels = [cat for cat in categories if category_totals[cat]['time'] > 0]
        pie_values = [category_totals[cat]['time'] for cat in pie_labels]
        pie_colors = [colors[i] for i, cat in enumerate(categories) if category_totals[cat]['time'] > 0]
        
        ax2.pie(pie_values, labels=pie_labels, autopct='%1.1f%%', 
                colors=pie_colors, startangle=90)
        ax2.set_title('Workout Distribution (%)')
    else:
        ax1.text(0.5, 0.5, 'No workout data', ha='center', va='center', transform=ax1.transAxes)
        ax2.text(0.5, 0.5, 'No workout data', ha='center', va='center', transform=ax2.transAxes)
    
    plt.tight_layout()
    
    # Convert to base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return jsonify({'chart': plot_url})

@app.route('/export_pdf')
def export_pdf():
    """Generate and download weekly PDF report"""
    if not tracker.user_info:
        flash('Please save user info first!', 'danger')
        return redirect(url_for('index'))
    
    try:
        filename = f"{tracker.user_info['name'].replace(' ', '_')}_weekly_report.pdf"
        filepath = os.path.join('/tmp', filename)
        
        c = pdf_canvas.Canvas(filepath, pagesize=A4)
        width, height = A4
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height-50, f"Weekly Fitness Report - {tracker.user_info['name']}")
        
        # User Info
        c.setFont("Helvetica", 11)
        user = tracker.user_info
        c.drawString(50, height-80, f"Regn-ID: {user['regn_id']} | Age: {user['age']} | Gender: {user['gender']}")
        c.drawString(50, height-100, f"Height: {user['height']} cm | Weight: {user['weight']} kg | BMI: {user['bmi']:.1f} | BMR: {user['bmr']:.0f} kcal/day")
        
        # Table of workouts
        y = height-140
        table_data = [["Category", "Exercise", "Duration(min)", "Calories(kcal)", "Date"]]
        
        for cat, sessions in tracker.workouts.items():
            for entry in sessions:
                table_data.append([
                    cat,
                    entry['exercise'],
                    str(entry['duration']),
                    f"{entry['calories']:.1f}",
                    entry['timestamp'].split()[0]
                ])
        
        if len(table_data) > 1:
            table = Table(table_data, colWidths=[80, 150, 80, 80, 80])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), rl_colors.lightblue),
                ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.black)
            ]))
            table.wrapOn(c, width-100, y)
            table.drawOn(c, 50, y-len(table_data)*20)
        else:
            c.drawString(50, y, "No workouts recorded yet.")
        
        c.save()
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        flash(f'Error generating PDF: {e}', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)