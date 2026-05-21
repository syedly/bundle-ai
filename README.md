# Bundle AI Training Builder

A self-serve chatbot that guides HR leaders and executives through a structured conversation and produces a specific, role-by-role training plan using Bundle's real session catalog.

## Quick Start

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. Add your OpenAI API key
Open `.env` and set:
```
OPENAI_API_KEY=your-key-here
```

### 3. Add your Bundle logo
Place `bundle.png` in:
```
builder/static/builder/images/bundle.png
```
The app shows "BUNDLE" as text fallback if the image is missing.

### 4. Set up the database
```
python manage.py migrate
python manage.py seed_data
```

### 5. Create an admin user (optional)
```
python manage.py createsuperuser
```

### 6. Run
```
python manage.py runserver
```

Visit: http://127.0.0.1:8000

Admin panel: http://127.0.0.1:8000/admin/

## What it does

1. CEO clicks **Get Started**
2. Answers 6 questions about their company (with smart toggle buttons)
3. Pastes performance data, job descriptions, or answers 8 diagnostic questions
4. Receives a typed-out AI analysis with 3 specific scenario options
5. Selects a scenario and picks a session count (4 / 6 / 8 / 10)
6. Receives a full training plan with named sessions and per-session reasoning
7. Books a consultation — selects date and time
8. Sees a confirmation page

## Tech Stack

- **Backend:** Django 4.2+ (MVT)
- **Database:** SQLite
- **AI:** OpenAI gpt-4o
- **Frontend:** Plain HTML + CSS + JavaScript (no frameworks)
