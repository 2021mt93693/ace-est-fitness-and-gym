import pytest
from datetime import datetime
from src.app import WorkoutManager

@pytest.fixture
def manager():
    return WorkoutManager()

# Test backward compatibility with old method signature
def test_add_workout_success_old_signature(manager):
    manager.add_workout("Running", 30)
    workouts = manager.get_workouts()
    assert len(workouts) == 1
    assert workouts[0]["exercise"] == "Running"
    assert workouts[0]["duration"] == 30
    assert workouts[0]["category"] == "Workout"  # Default category
    assert "timestamp" in workouts[0]

# Test new method signature with category
def test_add_workout_success_with_category(manager):
    manager.add_workout("Jumping Jacks", 10, "Warm-up")
    workouts = manager.get_workouts()
    assert len(workouts) == 1
    assert workouts[0]["exercise"] == "Jumping Jacks"
    assert workouts[0]["duration"] == 10
    assert workouts[0]["category"] == "Warm-up"
    assert "timestamp" in workouts[0]

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
        manager.add_workout("Push-ups", 15, "Invalid")

def test_get_workouts_empty(manager):
    assert manager.get_workouts() == []

def test_get_workouts_multiple(manager):
    manager.add_workout("Yoga", 45, "Cool-down")
    manager.add_workout("HIIT", 20, "Workout")
    workouts = manager.get_workouts()
    assert len(workouts) == 2
    # Check that both workouts are in the flat list
    exercise_names = [w["exercise"] for w in workouts]
    assert "Yoga" in exercise_names
    assert "HIIT" in exercise_names

def test_get_workouts_by_category(manager):
    manager.add_workout("Stretching", 10, "Warm-up")
    manager.add_workout("Push-ups", 15, "Workout")
    manager.add_workout("Deep Breathing", 5, "Cool-down")
    
    workouts_by_category = manager.get_workouts_by_category()
    assert len(workouts_by_category["Warm-up"]) == 1
    assert len(workouts_by_category["Workout"]) == 1
    assert len(workouts_by_category["Cool-down"]) == 1
    
    assert workouts_by_category["Warm-up"][0]["exercise"] == "Stretching"
    assert workouts_by_category["Workout"][0]["exercise"] == "Push-ups"
    assert workouts_by_category["Cool-down"][0]["exercise"] == "Deep Breathing"

def test_get_total_time(manager):
    manager.add_workout("Exercise1", 10, "Warm-up")
    manager.add_workout("Exercise2", 20, "Workout")
    manager.add_workout("Exercise3", 15, "Cool-down")
    
    total_time = manager.get_total_time()
    assert total_time == 45

def test_get_total_time_empty(manager):
    assert manager.get_total_time() == 0

def test_get_category_totals(manager):
    manager.add_workout("Exercise1", 10, "Warm-up")
    manager.add_workout("Exercise2", 20, "Workout")
    manager.add_workout("Exercise3", 5, "Workout")
    manager.add_workout("Exercise4", 15, "Cool-down")
    
    category_totals = manager.get_category_totals()
    assert category_totals["Warm-up"] == 10
    assert category_totals["Workout"] == 25
    assert category_totals["Cool-down"] == 15

def test_get_exercise_suggestions(manager):
    # Test default category
    suggestions = manager.get_exercise_suggestions()
    assert isinstance(suggestions, list)
    assert "Push-ups" in suggestions
    
    # Test specific category
    warmup_suggestions = manager.get_exercise_suggestions("Warm-up")
    assert isinstance(warmup_suggestions, list)
    assert "Jumping Jacks" in warmup_suggestions
    
    # Test invalid category
    invalid_suggestions = manager.get_exercise_suggestions("Invalid")
    assert invalid_suggestions == []

def test_get_diet_plans(manager):
    diet_plans = manager.get_diet_plans()
    assert isinstance(diet_plans, dict)
    assert "Weight Loss" in diet_plans
    assert "Muscle Gain" in diet_plans
    assert "Endurance" in diet_plans
    
    # Test that it's a copy (immutable)
    original_count = len(diet_plans["Weight Loss"])
    diet_plans["Weight Loss"].append("Test Food")
    fresh_diet_plans = manager.get_diet_plans()
    assert len(fresh_diet_plans["Weight Loss"]) == original_count

def test_timestamp_format(manager):
    manager.add_workout("Test Exercise", 10)
    workouts = manager.get_workouts()
    
    # Check that timestamp is in correct format
    timestamp = workouts[0]["timestamp"]
    # Should be able to parse it back to datetime
    parsed_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    assert isinstance(parsed_time, datetime)

def test_multiple_exercises_same_category(manager):
    manager.add_workout("Exercise1", 10, "Workout")
    manager.add_workout("Exercise2", 15, "Workout")
    manager.add_workout("Exercise3", 20, "Workout")
    
    workouts_by_category = manager.get_workouts_by_category()
    assert len(workouts_by_category["Workout"]) == 3
    
    total_workout_time = sum(w["duration"] for w in workouts_by_category["Workout"])
    assert total_workout_time == 45