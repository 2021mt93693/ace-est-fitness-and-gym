import pytest
from src.app import FitnessTracker

@pytest.fixture
def tracker():
    return FitnessTracker()

@pytest.fixture
def tracker_with_user():
    tracker = FitnessTracker()
    tracker.save_user_info("John Doe", "2021MT001", 25, "M", 175.0, 70.0)
    return tracker

# User Info Tests
def test_save_user_info_success(tracker):
    result = tracker.save_user_info("Jane Smith", "2021MT002", 30, "F", 165.0, 60.0)
    assert result is True
    user_info = tracker.get_user_info()
    assert user_info["name"] == "Jane Smith"
    assert user_info["regn_id"] == "2021MT002"
    assert user_info["age"] == 30
    assert user_info["gender"] == "F"
    assert user_info["height"] == 165.0
    assert user_info["weight"] == 60.0
    assert "bmi" in user_info
    assert "bmr" in user_info

def test_save_user_info_calculate_bmi_bmr(tracker):
    tracker.save_user_info("Test User", "TEST001", 25, "M", 180.0, 80.0)
    user_info = tracker.get_user_info()
    # BMI = weight(kg) / height(m)^2 = 80 / (1.8)^2 = 24.69
    assert abs(user_info["bmi"] - 24.69) < 0.01
    # BMR for male = 10*weight + 6.25*height - 5*age + 5 = 10*80 + 6.25*180 - 5*25 + 5 = 1805
    assert abs(user_info["bmr"] - 1805) < 1

def test_save_user_info_missing_fields(tracker):
    with pytest.raises(ValueError):
        tracker.save_user_info("", "ID001", 25, "M", 175.0, 70.0)
    
    with pytest.raises(ValueError):
        tracker.save_user_info("John", "", 25, "M", 175.0, 70.0)

def test_save_user_info_invalid_gender(tracker):
    with pytest.raises(ValueError, match="Gender must be M or F"):
        tracker.save_user_info("John", "ID001", 25, "X", 175.0, 70.0)

def test_save_user_info_invalid_types(tracker):
    with pytest.raises(ValueError):
        tracker.save_user_info("John", "ID001", "twenty", "M", 175.0, 70.0)

# Workout Tests
def test_add_workout_success(tracker_with_user):
    entry = tracker_with_user.add_workout("Workout", "Running", 30)
    assert entry["exercise"] == "Running"
    assert entry["duration"] == 30
    assert "calories" in entry
    assert "timestamp" in entry
    
    workouts = tracker_with_user.get_workouts()
    assert len(workouts["Workout"]) == 1
    assert workouts["Workout"][0]["exercise"] == "Running"

def test_add_workout_calorie_calculation(tracker_with_user):
    # User weight is 70kg, Workout category has MET=6
    # Formula: (MET * 3.5 * weight / 200) * duration
    # (6 * 3.5 * 70 / 200) * 30 = 220.5 calories
    entry = tracker_with_user.add_workout("Workout", "Cycling", 30)
    expected_calories = (6 * 3.5 * 70 / 200) * 30
    assert abs(entry["calories"] - expected_calories) < 0.1

def test_add_workout_different_categories(tracker_with_user):
    tracker_with_user.add_workout("Warm-up", "Stretching", 10)
    tracker_with_user.add_workout("Workout", "Weight Training", 45)
    tracker_with_user.add_workout("Cool-down", "Walking", 15)
    
    workouts = tracker_with_user.get_workouts()
    assert len(workouts["Warm-up"]) == 1
    assert len(workouts["Workout"]) == 1
    assert len(workouts["Cool-down"]) == 1
    assert workouts["Warm-up"][0]["exercise"] == "Stretching"
    assert workouts["Workout"][0]["exercise"] == "Weight Training"
    assert workouts["Cool-down"][0]["exercise"] == "Walking"

def test_add_workout_missing_exercise(tracker):
    with pytest.raises(ValueError, match="Exercise and duration are required"):
        tracker.add_workout("Workout", "", 20)

def test_add_workout_missing_duration(tracker):
    with pytest.raises(ValueError, match="Exercise and duration are required"):
        tracker.add_workout("Workout", "Running", None)

def test_add_workout_invalid_duration(tracker):
    with pytest.raises(ValueError, match="Duration must be a positive integer"):
        tracker.add_workout("Workout", "Running", 0)
    
    with pytest.raises(ValueError, match="Duration must be a positive integer"):
        tracker.add_workout("Workout", "Running", -5)

def test_add_workout_invalid_category(tracker):
    with pytest.raises(ValueError, match="Invalid category"):
        tracker.add_workout("InvalidCategory", "Running", 30)

def test_add_workout_without_user_info(tracker):
    # Should work with default weight
    entry = tracker.add_workout("Workout", "Running", 30)
    assert entry["exercise"] == "Running"
    assert entry["duration"] == 30
    assert entry["calories"] > 0  # Should calculate calories with default weight (70kg)

# Summary Tests
def test_get_workout_summary_empty(tracker):
    summary = tracker.get_workout_summary()
    assert summary["total_time"] == 0
    assert summary["total_calories"] == 0
    assert all(cat["time"] == 0 for cat in summary["category_totals"].values())

def test_get_workout_summary_with_workouts(tracker_with_user):
    tracker_with_user.add_workout("Warm-up", "Stretching", 10)
    tracker_with_user.add_workout("Workout", "Running", 30)
    tracker_with_user.add_workout("Cool-down", "Walking", 15)
    
    summary = tracker_with_user.get_workout_summary()
    assert summary["total_time"] == 55
    assert summary["total_calories"] > 0
    assert summary["category_totals"]["Warm-up"]["time"] == 10
    assert summary["category_totals"]["Workout"]["time"] == 30
    assert summary["category_totals"]["Cool-down"]["time"] == 15
    assert summary["category_totals"]["Warm-up"]["sessions"] == 1
    assert summary["category_totals"]["Workout"]["sessions"] == 1
    assert summary["category_totals"]["Cool-down"]["sessions"] == 1

def test_get_workouts_returns_copy(tracker_with_user):
    tracker_with_user.add_workout("Workout", "Running", 30)
    workouts1 = tracker_with_user.get_workouts()
    workouts2 = tracker_with_user.get_workouts()
    
    # Should be separate copies
    assert workouts1 is not workouts2
    assert workouts1 == workouts2
    
    # Modifying returned dict shouldn't affect original
    workouts1["NewCategory"] = []
    workouts3 = tracker_with_user.get_workouts()
    assert "NewCategory" not in workouts3

def test_get_user_info_returns_copy(tracker_with_user):
    user_info1 = tracker_with_user.get_user_info()
    user_info2 = tracker_with_user.get_user_info()
    
    # Should be separate copies
    assert user_info1 is not user_info2
    assert user_info1 == user_info2
    
    # Modifying returned dict shouldn't affect original
    user_info1["name"] = "Modified Name"
    user_info3 = tracker_with_user.get_user_info()
    assert user_info3["name"] == "John Doe"

# Integration Tests
def test_multiple_workouts_same_category(tracker_with_user):
    tracker_with_user.add_workout("Workout", "Running", 30)
    tracker_with_user.add_workout("Workout", "Cycling", 45)
    tracker_with_user.add_workout("Workout", "Swimming", 60)
    
    workouts = tracker_with_user.get_workouts()
    assert len(workouts["Workout"]) == 3
    
    summary = tracker_with_user.get_workout_summary()
    assert summary["total_time"] == 135
    assert summary["category_totals"]["Workout"]["sessions"] == 3
    assert summary["category_totals"]["Workout"]["time"] == 135

def test_bmr_calculation_female(tracker):
    tracker.save_user_info("Jane", "ID001", 30, "F", 165.0, 55.0)
    user_info = tracker.get_user_info()
    # BMR for female = 10*weight + 6.25*height - 5*age - 161
    # = 10*55 + 6.25*165 - 5*30 - 161 = 550 + 1031.25 - 150 - 161 = 1270.25
    expected_bmr = 10*55 + 6.25*165 - 5*30 - 161
    assert abs(user_info["bmr"] - expected_bmr) < 0.1