import pytest
from src.app import WorkoutManager
from datetime import datetime

@pytest.fixture
def manager():
    return WorkoutManager()

# Original functionality tests
def test_add_workout_success(manager):
    manager.add_workout("Running", 30)
    workouts = manager.get_workouts()
    assert len(workouts["Workout"]) == 1
    assert workouts["Workout"][0]["exercise"] == "Running"
    assert workouts["Workout"][0]["duration"] == 30
    assert "timestamp" in workouts["Workout"][0]

def test_add_workout_missing_exercise(manager):
    with pytest.raises(ValueError):
        manager.add_workout("", 20)

def test_add_workout_missing_duration(manager):
    with pytest.raises(ValueError):
        manager.add_workout("Cycling", None)

def test_add_workout_non_integer_duration(manager):
    with pytest.raises(TypeError):
        manager.add_workout("Swimming", "forty")

def test_add_workout_negative_duration(manager):
    with pytest.raises(ValueError):
        manager.add_workout("Yoga", -10)

def test_add_workout_zero_duration(manager):
    with pytest.raises(ValueError):
        manager.add_workout("Stretching", 0)

def test_get_workouts_empty(manager):
    workouts = manager.get_workouts()
    assert workouts == {"Warm-up": [], "Workout": [], "Cool-down": []}

def test_get_workouts_multiple(manager):
    manager.add_workout("Yoga", 45, "Workout")
    manager.add_workout("HIIT", 20, "Workout")
    workouts = manager.get_workouts()
    assert len(workouts["Workout"]) == 2
    assert workouts["Workout"][1]["exercise"] == "HIIT"
    assert workouts["Workout"][1]["duration"] == 20

# New functionality tests for categories
def test_add_workout_with_category_warm_up(manager):
    manager.add_workout("Jumping Jacks", 5, "Warm-up")
    workouts = manager.get_workouts()
    assert len(workouts["Warm-up"]) == 1
    assert workouts["Warm-up"][0]["exercise"] == "Jumping Jacks"
    assert workouts["Warm-up"][0]["duration"] == 5

def test_add_workout_with_category_cool_down(manager):
    manager.add_workout("Stretching", 10, "Cool-down")
    workouts = manager.get_workouts()
    assert len(workouts["Cool-down"]) == 1
    assert workouts["Cool-down"][0]["exercise"] == "Stretching"
    assert workouts["Cool-down"][0]["duration"] == 10

def test_add_workout_invalid_category(manager):
    with pytest.raises(ValueError):
        manager.add_workout("Running", 30, "InvalidCategory")

def test_default_category_is_workout(manager):
    manager.add_workout("Push-ups", 15)  # No category specified
    workouts = manager.get_workouts()
    assert len(workouts["Workout"]) == 1
    assert workouts["Workout"][0]["exercise"] == "Push-ups"

# Tests for new methods
def test_get_all_workouts_flat(manager):
    manager.add_workout("Warm-up Exercise", 5, "Warm-up")
    manager.add_workout("Main Exercise", 30, "Workout")
    manager.add_workout("Cool-down Exercise", 10, "Cool-down")
    
    flat_workouts = manager.get_all_workouts_flat()
    assert len(flat_workouts) == 3
    
    # Check first workout
    assert flat_workouts[0]["workout"] == "Warm-up Exercise"
    assert flat_workouts[0]["category"] == "Warm-up"
    assert flat_workouts[0]["duration"] == 5
    assert "timestamp" in flat_workouts[0]

def test_get_totals_by_category(manager):
    manager.add_workout("Warm-up 1", 5, "Warm-up")
    manager.add_workout("Warm-up 2", 10, "Warm-up")
    manager.add_workout("Main Exercise", 30, "Workout")
    manager.add_workout("Cool-down", 5, "Cool-down")
    
    totals = manager.get_totals_by_category()
    assert totals["Warm-up"] == 15
    assert totals["Workout"] == 30
    assert totals["Cool-down"] == 5

def test_get_totals_by_category_empty(manager):
    totals = manager.get_totals_by_category()
    assert totals["Warm-up"] == 0
    assert totals["Workout"] == 0
    assert totals["Cool-down"] == 0

def test_get_total_time(manager):
    manager.add_workout("Exercise 1", 15, "Warm-up")
    manager.add_workout("Exercise 2", 30, "Workout")
    manager.add_workout("Exercise 3", 10, "Cool-down")
    
    total = manager.get_total_time()
    assert total == 55

def test_get_total_time_empty(manager):
    total = manager.get_total_time()
    assert total == 0

def test_has_workouts_true(manager):
    manager.add_workout("Test Exercise", 20)
    assert manager.has_workouts() == True

def test_has_workouts_false(manager):
    assert manager.has_workouts() == False

def test_timestamp_format(manager):
    manager.add_workout("Test", 10)
    workouts = manager.get_workouts()
    timestamp = workouts["Workout"][0]["timestamp"]
    
    # Check timestamp format: YYYY-MM-DD HH:MM:SS
    try:
        datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pytest.fail("Timestamp format is incorrect")

# Integration tests
def test_multiple_categories_integration(manager):
    # Add workouts to all categories
    manager.add_workout("Warm-up", 10, "Warm-up")
    manager.add_workout("Strength Training", 45, "Workout")
    manager.add_workout("Cardio", 20, "Workout")
    manager.add_workout("Stretching", 15, "Cool-down")
    
    # Test all methods work correctly
    workouts = manager.get_workouts()
    assert len(workouts["Warm-up"]) == 1
    assert len(workouts["Workout"]) == 2
    assert len(workouts["Cool-down"]) == 1
    
    flat_workouts = manager.get_all_workouts_flat()
    assert len(flat_workouts) == 4
    
    totals = manager.get_totals_by_category()
    assert totals["Warm-up"] == 10
    assert totals["Workout"] == 65
    assert totals["Cool-down"] == 15
    
    total_time = manager.get_total_time()
    assert total_time == 90
    
    assert manager.has_workouts() == True