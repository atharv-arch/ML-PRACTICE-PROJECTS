# Daily Routine Optimizer

A cross-platform personal productivity prototype that combines task scheduling, completion tracking, analytics, and machine-learning based alarm optimization.

## Tech Stack
- **Frontend**: Streamlit
- **Backend API**: FastAPI
- **Database**: SQLite
- **ML/Analytics**: Pandas + Scikit-Learn
- **CI**: GitHub Actions

## Folder Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── services/
│   │       ├── analytics.py
│   │       ├── ml.py
│   │       └── preprocess.py
│   └── scripts/
│       └── train_model.py
├── data/
│   └── sample_tasks.csv
├── frontend/
│   └── streamlit_app.py
├── models/                # created after training
│   ├── best_time_model.joblib
│   └── plots/
├── tests/
│   ├── test_analytics.py
│   └── test_api.py
├── .github/workflows/
│   └── ci.yml
└── requirements.txt
```

## Features
1. **Task Input & Tracking**
   - Add task title, description, priority, type, assigned time, duration, reminder.
   - Mark tasks pending/completed.
   - Usage log records creation + status events.

2. **Analytics Engine**
   - Completion % by task type.
   - Most productive hours from completion timestamps.
   - Average delay, missed tasks, streak days.
   - Week-over-week completion trend.

3. **AI/ML Suggestion Module**
   - Trains RandomForest and LogisticRegression models.
   - Selects best model by validation accuracy.
   - Predicts best completion hour for pending tasks.
   - Suggests optimized alarm hour + priority.

4. **UI**
   - Dashboard with completion stats and charts.
   - Schedule table (calendar-like view of assigned tasks).
   - AI suggestion panel.

## API Endpoints
- `GET /health`
- `POST /tasks`
- `GET /tasks?status=pending|completed`
- `PATCH /tasks/{id}/status`
- `GET /analytics`
- `POST /ml/train`
- `GET /ml/suggestions`

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Start backend
```bash
uvicorn backend.app.main:app --reload
```

### Start frontend
```bash
streamlit run frontend/streamlit_app.py
```

## Train the Model + Generate Plots

```bash
python backend/scripts/train_model.py --input data/sample_tasks.csv
```

This creates:
- `models/best_time_model.joblib`
- `models/plots/productivity_by_hour.png`
- `models/plots/week_over_week_completion.png`

## Testing

```bash
pytest -q
```

## Sample Dataset Format
Use `data/sample_tasks.csv` with columns:
- `id, title, description, priority, task_type, assigned_time, duration_minutes, reminder_minutes_before, status, completed_at`

## Task Recommendation Logic
1. Preprocess historical records (handle missing values, derive weekday/hour/delay features).
2. Filter completed tasks to learn real behavior.
3. Train models on `priority`, `duration_minutes`, `assigned_weekday`, `task_type`.
4. Predict the best completion hour for each pending task.
5. If no trained model exists, fallback to top productive hours from analytics.
6. Return recommendation with explanation and suggested priority.
