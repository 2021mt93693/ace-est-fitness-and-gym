import pytest
from src.app import WorkoutManager

@pytest.fixture
def manager():
    return WorkoutManager()

def test_add_workout_success(manager):
    manager.add_workout("Running", 30)
    workouts = manager.get_workouts()
    assert len(workouts) == 1
    assert workouts[0]["workout"] == "Running"
    assert workouts[0]["duration"] == 30

def test_add_workout_missing_workout(manager):
    with pytest.raises(ValueError):
        manager.add_workout("", 20)

def test_add_workout_missing_duration(manager):
    with pytest.raises(ValueError):
        manager.add_workout("Cycling", None)

def test_add_workout_non_integer_duration(manager):
    with pytest.raises(TypeError):
        manager.add_workout("Swimming", "forty")

def test_get_workouts_empty(manager):
    assert manager.get_workouts() == []

def test_get_workouts_multiple(manager):
    manager.add_workout("Yoga", 45)
    manager.add_workout("HIIT", 20)
    workouts = manager.get_workouts()
    assert len(workouts) == 2
    assert workouts[1]["workout"] == "HIIT"
    assert workouts[1]["duration"] == 20