import pytest
from src.app import WorkoutManager
from datetime import datetime

@pytest.fixture
def manager():
    return WorkoutManager()

def test_add_workout_success(manager):
    manager.add_workout("Running", 30)
    workouts = manager.get_workouts()
    assert len(workouts["Workout"]) == 1
    assert workouts["Workout"][0]["exercise"] == "Running"
    assert workouts["Workout"][0]["duration"] == 30
    assert workouts["Workout"][0]["category"] == "Workout"
    assert "timestamp" in workouts["Workout"][0]

def test_add_workout_with_category(manager):
    manager.add_workout("Stretching", 10, "Warm-up")
    workouts = manager.get_workouts()
    assert len(workouts["Warm-up"]) == 1
    assert workouts["Warm-up"][0]["exercise"] == "Stretching"
    assert workouts["Warm-up"][0]["category"] == "Warm-up"

def test_add_workout_missing_workout(manager):
    with pytest.raises(ValueError, match="Workout and duration are required"):
        manager.add_workout("", 20)

def test_add_workout_missing_duration(manager):
    with pytest.raises(ValueError, match="Workout and duration are required"):
        manager.add_workout("Cycling", None)

def test_add_workout_non_integer_duration(manager):
    with pytest.raises(TypeError, match="Duration must be an integer"):
        manager.add_workout("Swimming", "forty")

def test_add_workout_negative_duration(manager):
    with pytest.raises(ValueError, match="Duration must be positive"):
        manager.add_workout("Plank", -5)

def test_add_workout_zero_duration(manager):
    with pytest.raises(ValueError, match="Duration must be positive"):
        manager.add_workout("Rest", 0)

def test_add_workout_invalid_category(manager):
    with pytest.raises(ValueError, match="Invalid category"):
        manager.add_workout("Running", 30, "InvalidCategory")

def test_get_workouts_empty(manager):
    workouts = manager.get_workouts()
    assert workouts == {"Warm-up": [], "Workout": [], "Cool-down": []}

def test_get_workouts_multiple_categories(manager):
    manager.add_workout("Jumping Jacks", 5, "Warm-up")
    manager.add_workout("Push-ups", 15, "Workout")
    manager.add_workout("Stretching", 10, "Cool-down")
    
    workouts = manager.get_workouts()
    assert len(workouts["Warm-up"]) == 1
    assert len(workouts["Workout"]) == 1
    assert len(workouts["Cool-down"]) == 1
    assert workouts["Warm-up"][0]["exercise"] == "Jumping Jacks"
    assert workouts["Workout"][0]["exercise"] == "Push-ups"
    assert workouts["Cool-down"][0]["exercise"] == "Stretching"

def test_get_all_workouts_flat(manager):
    manager.add_workout("Yoga", 45, "Warm-up")
    manager.add_workout("HIIT", 20, "Workout")
    
    flat_workouts = manager.get_all_workouts_flat()
    assert len(flat_workouts) == 2
    assert flat_workouts[0]["workout"] == "Yoga"
    assert flat_workouts[0]["category"] == "Warm-up"
    assert flat_workouts[1]["workout"] == "HIIT"
    assert flat_workouts[1]["category"] == "Workout"

def test_get_progress_data(manager):
    manager.add_workout("Running", 30, "Workout")
    manager.add_workout("Warm-up", 10, "Warm-up")
    manager.add_workout("Cool-down", 5, "Cool-down")
    
    progress_data = manager.get_progress_data()
    assert progress_data["Workout"] == 30
    assert progress_data["Warm-up"] == 10
    assert progress_data["Cool-down"] == 5

def test_get_workout_summary(manager):
    manager.add_workout("Running", 30, "Workout")
    manager.add_workout("Walking", 20, "Workout")
    manager.add_workout("Stretching", 10, "Warm-up")
    
    summary = manager.get_workout_summary()
    assert summary["total_time"] == 60
    assert summary["Workout"]["total_time"] == 50
    assert summary["Workout"]["count"] == 2
    assert summary["Warm-up"]["total_time"] == 10
    assert summary["Warm-up"]["count"] == 1
    assert summary["Cool-down"]["total_time"] == 0
    assert summary["Cool-down"]["count"] == 0

def test_workout_timestamps(manager):
    manager.add_workout("Running", 30)
    workouts = manager.get_workouts()
    timestamp = workouts["Workout"][0]["timestamp"]
    
    # Check timestamp format
    try:
        datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        timestamp_valid = True
    except ValueError:
        timestamp_valid = False
    
    assert timestamp_valid

def test_multiple_workouts_same_category(manager):
    manager.add_workout("Push-ups", 15, "Workout")
    manager.add_workout("Squats", 20, "Workout")
    manager.add_workout("Planks", 10, "Workout")
    
    workouts = manager.get_workouts()
    assert len(workouts["Workout"]) == 3
    assert workouts["Workout"][0]["exercise"] == "Push-ups"
    assert workouts["Workout"][1]["exercise"] == "Squats"
    assert workouts["Workout"][2]["exercise"] == "Planks"

def test_get_workouts_returns_copy(manager):
    manager.add_workout("Running", 30)
    workouts1 = manager.get_workouts()
    workouts2 = manager.get_workouts()
    
    # Modify one copy
    workouts1["Workout"].append({"exercise": "Test", "duration": 10})
    
    # Original should be unchanged
    assert len(workouts2["Workout"]) == 1
    assert len(manager.get_workouts()["Workout"]) == 1