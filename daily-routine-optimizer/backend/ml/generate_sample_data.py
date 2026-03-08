"""
Sample Data Generator — Creates realistic task data for ML training.

Generates 4 weeks of daily task data with realistic patterns:
    - Morning person bias (more completions 8-12)
    - Category-specific timing patterns
    - Realistic completion delays and miss rates
    - Priority distribution following Pareto principle

Usage:
    python -m ml.generate_sample_data
"""

import os
import csv
import random
from datetime import datetime, timedelta

# ── Configuration ──────────────────────────────────────────────────────────

CATEGORIES = ["work", "health", "personal", "learning", "errands"]
TASK_TEMPLATES = {
    "work": [
        "Review pull requests", "Team standup meeting", "Write documentation",
        "Fix bug in module", "Code review session", "Sprint planning",
        "Email inbox zero", "Prepare presentation", "Database optimization",
        "API integration testing",
    ],
    "health": [
        "Morning jog", "Gym workout", "Yoga session", "Meal prep",
        "Meditation", "Evening walk", "Stretching routine", "Drink water log",
    ],
    "personal": [
        "Read book chapter", "Journal writing", "Call family",
        "Household cleaning", "Budget review", "Grocery shopping",
    ],
    "learning": [
        "Online course lecture", "Practice coding problems", "Read tech article",
        "Study for certification", "Watch tutorial video", "Side project work",
    ],
    "errands": [
        "Bank visit", "Post office", "Car maintenance", "Dentist appointment",
        "Pick up dry cleaning", "Pay bills",
    ],
}

# Productivity patterns: (hour, relative_probability)
# Simulates a "morning person" with afternoon dip
HOUR_WEIGHTS = {
    6: 0.3, 7: 0.5, 8: 0.8, 9: 1.0, 10: 0.95, 11: 0.9,
    12: 0.5, 13: 0.4, 14: 0.6, 15: 0.7, 16: 0.65, 17: 0.5,
    18: 0.4, 19: 0.3, 20: 0.25, 21: 0.2, 22: 0.1,
}

# Completion probability by priority (higher priority = more likely to complete)
PRIORITY_COMPLETION = {1: 0.5, 2: 0.6, 3: 0.7, 4: 0.85, 5: 0.95}


def generate_sample_data(num_weeks: int = 4, output_dir: str = None):
    """
    Generate a CSV dataset of sample task data.

    Args:
        num_weeks: Number of weeks of data to generate (default: 4)
        output_dir: Directory to save the CSV file

    Returns:
        Path to the generated CSV file
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "sample_tasks.csv")

    rows = []
    start_date = datetime.utcnow() - timedelta(weeks=num_weeks)

    for day_offset in range(num_weeks * 7):
        current_date = start_date + timedelta(days=day_offset)
        day_of_week = current_date.weekday()

        # Generate 4-8 tasks per day (fewer on weekends)
        tasks_per_day = random.randint(4, 8) if day_of_week < 5 else random.randint(2, 4)

        for _ in range(tasks_per_day):
            # Pick a random category and task template
            category = random.choice(CATEGORIES)
            title = random.choice(TASK_TEMPLATES[category])

            # Assign priority (follows Pareto: most are medium)
            priority = random.choices([1, 2, 3, 4, 5], weights=[10, 30, 35, 15, 10])[0]

            # Pick an assigned hour based on productivity weights
            hours = list(HOUR_WEIGHTS.keys())
            weights = list(HOUR_WEIGHTS.values())
            assigned_hour = random.choices(hours, weights=weights)[0]
            assigned_time = current_date.replace(
                hour=assigned_hour,
                minute=random.choice([0, 15, 30, 45]),
                second=0, microsecond=0,
            )

            # Duration: 15-120 minutes, influenced by category
            duration_map = {
                "work": (30, 120), "health": (20, 60), "personal": (15, 45),
                "learning": (30, 90), "errands": (15, 60),
            }
            dur_min, dur_max = duration_map[category]
            duration = random.randint(dur_min // 15, dur_max // 15) * 15

            # Determine completion
            base_probability = PRIORITY_COMPLETION[priority]
            # Time-of-day modifier
            hour_modifier = HOUR_WEIGHTS.get(assigned_hour, 0.3)
            completion_prob = min(1.0, base_probability * (0.5 + 0.5 * hour_modifier))

            completed = random.random() < completion_prob
            status = "completed" if completed else random.choice(["missed", "pending"])

            # Completion time with realistic delay
            completed_at = None
            delay_minutes = 0
            if completed:
                # Most tasks completed within 0-45 min of assigned time
                delay_minutes = int(random.gauss(10, 20))
                delay_minutes = max(-15, min(90, delay_minutes))  # Clamp
                completed_at = assigned_time + timedelta(minutes=duration + delay_minutes)

            rows.append({
                "title": title,
                "description": f"Auto-generated {category} task",
                "category": category,
                "priority": priority,
                "assigned_time": assigned_time.isoformat(),
                "duration_minutes": duration,
                "reminder_minutes_before": random.choice([5, 10, 15, 30]),
                "status": status,
                "completed_at": completed_at.isoformat() if completed_at else "",
                "created_at": (assigned_time - timedelta(hours=random.randint(1, 24))).isoformat(),
                "day_of_week": day_of_week,
                "assigned_hour": assigned_hour,
                "delay_minutes": delay_minutes if completed else "",
            })

    # Write to CSV
    fieldnames = list(rows[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Generated {len(rows)} sample tasks over {num_weeks} weeks")
    print(f"📁 Saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_sample_data()
