# Study_count_Telegram_bot
A Telegram bot built with Python to help users track their study hours and visualize their progress through automated charts.
---

## Features

- User registration
- Add multiple study subjects
- Record study hours per subject
- View daily progress chart
- View weekly overall progress chart
- View weekly chart per subject
- SQLite database storage
- Interactive Telegram keyboard menu

---

## Tech Stack

- Python 3
- pyTelegramBotAPI (telebot)
- SQLite3
- Matplotlib
- Schedule

---

## Project Structure

```
study-tracker-bot/
│
├── Study_count_bot.py
├── database.db
├── requirements.txt
├── README.md
└── .env
```

---

## Installation

Install dependencies:

pip install -r requirements.txt

## Run the Bot

```bash
python Study_count_bot.py
```

---

## Database Structure

### Users Table
| Column | Type |
|--------|------|
| id | INTEGER |
| telegram_id | INTEGER |
| name | TEXT |

### Subjects Table
| Column | Type |
|--------|------|
| id | INTEGER |
| user_id | INTEGER |
| subject_name | TEXT |

### Study Records Table
| Column | Type |
|--------|------|
| id | INTEGER |
| user_id | INTEGER |
| subject_id | INTEGER |
| hours | FLOAT |
| date | TEXT |

---

## Charts

The bot generates:
- Daily study chart
- Weekly overall chart
- Weekly subject-based chart
- Monthly overall chart
- Monthly subject-based chart

Charts are generated using Matplotlib and sent directly to Telegram.
---

## .gitignore

Recommended entries:

```
.env
__pycache__/
*.pyc
database.db
```

---

## Author

Fereshteh Bahadorykhalily

---
