import pytest
from datetime import datetime
from src.app import WorkoutManager

@pytest.fixture
def manager():
    return WorkoutManager()

def test_add_workout_success(manager):
    manager.add_workout("Running", 30, "Workout")
    workouts = manager.get_workouts()
    assert len(workouts["Workout"]) == 1
    assert workouts["Workout"][0]["exercise"] == "Running"
    assert workouts["Workout"][0]["duration"] == 30
    assert "timestamp" in workouts["Workout"][0]

def test_add_workout_with_category(manager):
    manager.add_workout("Stretching", 15, "Warm-up")
    workouts = manager.get_workouts()
    assert len(workouts["Warm-up"]) == 1
    assert workouts["Warm-up"][0]["exercise"] == "Stretching"
    assert workouts["Warm-up"][0]["duration"] == 15

def test_add_workout_default_category(manager):
    manager.add_workout("Push-ups", 20)
    workouts = manager.get_workouts()
    assert len(workouts["Workout"]) == 1
    assert workouts["Workout"][0]["exercise"] == "Push-ups"

def test_add_workout_missing_exercise(manager):
    with pytest.raises(ValueError, match="Exercise and duration are required"):
        manager.add_workout("", 20)

def test_add_workout_missing_duration(manager):
    with pytest.raises(ValueError, match="Exercise and duration are required"):
        manager.add_workout("Cycling", None)

def test_add_workout_non_integer_duration(manager):
    with pytest.raises(TypeError, match="Duration must be an integer"):
        manager.add_workout("Swimming", "forty")

def test_add_workout_invalid_category(manager):
    with pytest.raises(ValueError, match="Invalid category"):
        manager.add_workout("Running", 30, "Invalid")

def test_get_workouts_empty(manager):
    workouts = manager.get_workouts()
    assert workouts == {"Warm-up": [], "Workout": [], "Cool-down": []}

def test_get_workouts_multiple_categories(manager):
    manager.add_workout("Stretching", 10, "Warm-up")
    manager.add_workout("Running", 30, "Workout")
    manager.add_workout("Walking", 15, "Cool-down")
    
    workouts = manager.get_workouts()
    assert len(workouts["Warm-up"]) == 1
    assert len(workouts["Workout"]) == 1
    assert len(workouts["Cool-down"]) == 1
    assert workouts["Workout"][0]["exercise"] == "Running"

def test_get_all_sessions(manager):
    manager.add_workout("Yoga", 45, "Warm-up")
    manager.add_workout("HIIT", 20, "Workout")
    
    all_sessions = manager.get_all_sessions()
    assert len(all_sessions) == 2
    
    # Check that category is added to each session
    categories = [session['category'] for session in all_sessions]
    assert "Warm-up" in categories
    assert "Workout" in categories

def test_get_summary_empty(manager):
    summary = manager.get_summary()
    assert summary['total_time'] == 0
    assert summary['session_count'] == 0
    assert summary['motivation'] == "Good start! Keep moving 💪"

def test_get_summary_with_sessions(manager):
    manager.add_workout("Stretching", 10, "Warm-up")
    manager.add_workout("Running", 30, "Workout")
    manager.add_workout("Walking", 15, "Cool-down")
    
    summary = manager.get_summary()
    assert summary['total_time'] == 55
    assert summary['session_count'] == 3
    assert summary['categories']['Warm-up']['total_time'] == 10
    assert summary['categories']['Workout']['total_time'] == 30
    assert summary['categories']['Cool-down']['total_time'] == 15

def test_motivation_messages(manager):
    # Test different motivation levels
    summary = manager.get_summary()
    assert summary['motivation'] == "Good start! Keep moving 💪"
    
    # Add 30 minutes - should trigger "Nice effort!" message since total_time >= 30
    manager.add_workout("Running", 30, "Workout")
    summary = manager.get_summary()
    assert summary['motivation'] == "Nice effort! You're building consistency 🔥"
    
    # Add more for 45 minutes total - should still be "Nice effort!" since < 60
    manager.add_workout("Cycling", 15, "Workout")
    summary = manager.get_summary()
    assert summary['motivation'] == "Nice effort! You're building consistency 🔥"
    
    # Add more for 75 minutes total - should trigger "Excellent dedication!" since >= 60
    manager.add_workout("Swimming", 30, "Workout")
    summary = manager.get_summary()
    assert summary['motivation'] == "Excellent dedication! Keep up the great work 🏆"

def test_workout_timestamp_format(manager):
    manager.add_workout("Test Exercise", 20, "Workout")
    workouts = manager.get_workouts()
    timestamp = workouts["Workout"][0]["timestamp"]
    
    # Check timestamp format (YYYY-MM-DD HH:MM:SS)
    try:
        datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        timestamp_valid = True
    except ValueError:
        timestamp_valid = False
    
    assert timestamp_valid