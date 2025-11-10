import pytest
from src.app import WorkoutManager
from datetime import datetime

@pytest.fixture
def manager():
    return WorkoutManager()

def test_add_workout_success(manager):
    manager.add_workout("Workout", "Running", 30)
    workouts = manager.get_workouts()
    assert len(workouts["Workout"]) == 1
    assert workouts["Workout"][0]["exercise"] == "Running"
    assert workouts["Workout"][0]["duration"] == 30
    assert "timestamp" in workouts["Workout"][0]

def test_add_workout_different_categories(manager):
    manager.add_workout("Warm-up", "Jumping Jacks", 5)
    manager.add_workout("Workout", "Push-ups", 15)
    manager.add_workout("Cool-down", "Stretching", 10)
    
    workouts = manager.get_workouts()
    assert len(workouts["Warm-up"]) == 1
    assert len(workouts["Workout"]) == 1
    assert len(workouts["Cool-down"]) == 1
    assert workouts["Warm-up"][0]["exercise"] == "Jumping Jacks"
    assert workouts["Workout"][0]["exercise"] == "Push-ups"
    assert workouts["Cool-down"][0]["exercise"] == "Stretching"

def test_add_workout_missing_workout(manager):
    with pytest.raises(ValueError, match="Workout and duration are required"):
        manager.add_workout("Workout", "", 20)

def test_add_workout_missing_duration(manager):
    with pytest.raises(ValueError, match="Workout and duration are required"):
        manager.add_workout("Workout", "Cycling", None)

def test_add_workout_non_integer_duration(manager):
    with pytest.raises(TypeError, match="Duration must be an integer"):
        manager.add_workout("Workout", "Swimming", "forty")

def test_add_workout_invalid_category(manager):
    with pytest.raises(ValueError, match="Invalid category"):
        manager.add_workout("Invalid", "Running", 30)

def test_get_workouts_empty(manager):
    workouts = manager.get_workouts()
    assert workouts == {"Warm-up": [], "Workout": [], "Cool-down": []}

def test_get_workouts_multiple(manager):
    manager.add_workout("Workout", "Yoga", 45)
    manager.add_workout("Workout", "HIIT", 20)
    workouts = manager.get_workouts()
    assert len(workouts["Workout"]) == 2
    assert workouts["Workout"][1]["exercise"] == "HIIT"
    assert workouts["Workout"][1]["duration"] == 20

def test_get_total_time_empty(manager):
    assert manager.get_total_time() == 0

def test_get_total_time_multiple_categories(manager):
    manager.add_workout("Warm-up", "Stretching", 10)
    manager.add_workout("Workout", "Running", 30)
    manager.add_workout("Cool-down", "Walking", 15)
    assert manager.get_total_time() == 55

def test_get_summary_empty(manager):
    summary = manager.get_summary()
    assert summary['total_time'] == 0
    assert summary['motivation'] == "Good start! Keep moving 💪"
    assert summary['workouts'] == {"Warm-up": [], "Workout": [], "Cool-down": []}

def test_get_summary_with_workouts(manager):
    manager.add_workout("Workout", "Running", 35)
    manager.add_workout("Workout", "Cycling", 25)
    summary = manager.get_summary()
    assert summary['total_time'] == 60
    assert summary['motivation'] == "Excellent dedication! Keep up the great work 🏆"

def test_get_summary_excellent_dedication(manager):
    manager.add_workout("Workout", "Running", 40)
    manager.add_workout("Workout", "Weight Training", 45)
    summary = manager.get_summary()
    assert summary['total_time'] == 85
    assert summary['motivation'] == "Excellent dedication! Keep up the great work 🏆"

def test_timestamp_format(manager):
    manager.add_workout("Workout", "Running", 30)
    workouts = manager.get_workouts()
    timestamp = workouts["Workout"][0]["timestamp"]
    # Check if timestamp is in the correct format
    try:
        datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        assert True
    except ValueError:
        assert False, "Timestamp format is incorrect"