# 🧠 Daily Routine Optimizer

An intelligent personal productivity app powered by machine learning. It helps you manage tasks, track completion patterns, and automatically suggests optimized schedules based on your behavior.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![License](https://img.shields.io/badge/license-MIT-purple)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Task Management** | Create, edit, complete, and delete tasks with priority and category |
| **Smart Analytics** | Hourly productivity, completion rates, streaks, and category breakdowns |
| **AI Schedule Optimizer** | ML model predicts your optimal task times based on past behavior |
| **Weekly Summaries** | Auto-generated performance reports with personalized recommendations |
| **Calendar View** | Monthly calendar with color-coded task status dots |
| **Premium Dark UI** | Glassmorphism design with smooth animations and Chart.js visualizations |

---

## 📁 Project Structure

```
ai_productive/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── database.py          # SQLite + SQLAlchemy setup
│   │   ├── models.py            # ORM models (Task, TaskLog, WeeklySummary)
│   │   ├── schemas.py           # Pydantic validation schemas
│   │   ├── utils.py             # Helper functions
│   │   ├── routers/
│   │   │   ├── tasks.py         # CRUD endpoints
│   │   │   ├── analytics.py     # Analytics endpoints
│   │   │   └── suggestions.py   # AI suggestion endpoints
│   │   └── services/
│   │       ├── analytics_engine.py  # Productivity calculations
│   │       └── ml_engine.py         # ML prediction service
│   ├── ml/
│   │   ├── generate_sample_data.py  # Sample dataset generator
│   │   ├── preprocessing.py        # Feature engineering
│   │   └── train_model.py          # Model training pipeline
│   ├── tests/
│   │   ├── test_tasks.py
│   │   ├── test_analytics.py
│   │   └── test_ml.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html               # SPA shell
│   ├── css/styles.css           # Design system
│   └── js/
│       ├── app.js               # SPA router
│       ├── api.js               # API client
│       ├── dashboard.js         # Dashboard view
│       ├── tasks.js             # Task management
│       ├── calendar.js          # Calendar view
│       ├── analytics.js         # Analytics charts
│       └── suggestions.js       # AI suggestions
├── .github/workflows/ci.yml    # CI/CD pipeline
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** installed
- **pip** package manager

### 1. Clone & Install

```bash
cd ai_productive
pip install -r backend/requirements.txt
```

### 2. Generate Sample Data & Train ML Model

```bash
cd backend
python -m ml.generate_sample_data
python -m ml.train_model
```

This generates 4 weeks of realistic task data and trains a classifier to predict optimal scheduling.

### 3. Run the Application

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. Open in Browser

- **App**: [http://localhost:8000](http://localhost:8000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## 🐳 Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
cd backend
docker build -t routine-optimizer .
docker run -p 8000:8000 routine-optimizer
```

---

## 📊 API Endpoints

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tasks/` | Create a task |
| GET | `/api/tasks/` | List tasks (with filters) |
| GET | `/api/tasks/{id}` | Get task details |
| PUT | `/api/tasks/{id}` | Update a task |
| PATCH | `/api/tasks/{id}/complete` | Mark task completed |
| DELETE | `/api/tasks/{id}` | Delete a task |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/dashboard` | Dashboard stats |
| GET | `/api/analytics/hourly` | Hourly productivity |
| GET | `/api/analytics/categories` | Category breakdown |
| GET | `/api/analytics/streaks` | Streak data |
| GET | `/api/analytics/weekly-summary` | Weekly summary |
| GET | `/api/analytics/weekly-comparison` | 4-week comparison |

### AI Suggestions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/suggestions/schedule` | AI-optimized schedule |
| GET | `/api/suggestions/insights` | Personalized insights |

---

## 🤖 Task Recommendations Logic

The AI module uses a two-tier approach:

### 1. ML-Based Predictions (when model is trained)
- **Algorithm**: Best of RandomForest / GradientBoosting / XGBoost
- **Features**: priority, duration, category, day_of_week, cyclical time encodings, historical completion rate
- **Target**: Optimal hour for task completion (0-23)
- **Selection**: Cross-validated on training data, best test accuracy wins

### 2. Rule-Based Fallback (before model training)
- **High priority (4-5)** → Schedule during most productive hour
- **Long tasks (60+ min)** → Schedule in the morning for peak focus
- **Low priority (1-2)** → Schedule in the afternoon
- **Medium priority** → Second most productive hour
- **Overlap avoidance**: Tasks are spread across different hours

### Insight Generation
- Peak performance window detection
- Category efficiency analysis
- Streak tracking with 80% completion threshold
- Delay pattern warnings
- Personalized improvement suggestions

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Backend | FastAPI, Python |
| Database | SQLite, SQLAlchemy |
| ML | scikit-learn, pandas, numpy, XGBoost |
| CI/CD | GitHub Actions |
| Deployment | Docker, Docker Compose |

---

## 📄 Sample Data Format

The sample dataset (`backend/data/sample_tasks.csv`) has these columns:

```csv
title,description,category,priority,assigned_time,duration_minutes,reminder_minutes_before,status,completed_at,created_at,day_of_week,assigned_hour,delay_minutes
```

---

## 📝 License

MIT License — feel free to use, modify, and distribute.
