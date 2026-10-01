# 📅 Deadline Tracker

Deadline Tracker is a Streamlit + Gemini vision application that reads a
syllabus, timetable, or assignment sheet, extracts important academic
deadlines, displays them clearly, and sends a deadline digest to a Telegram
bot.

## Flow

Upload document image
→ Gemini vision
→ Structured deadline extraction
→ Deadline dashboard
→ Telegram digest

## Requirements

- Python 3.9+
- Google AI Studio / Gemini API key
- Telegram account
- Telegram bot created using @BotFather

## Local setup

### 1. Create a virtual environment

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure secrets

Copy:

`.streamlit/secrets.toml.example`

to:

`.streamlit/secrets.toml`

Then add your real Gemini API key and Telegram bot token.

### 4. Create the Telegram bot

Open Telegram and message `@BotFather`.

Use:

`/newbot`

Follow the prompts and copy the bot token into `secrets.toml`.

Then open your new bot and send it any message. Telegram requires the
recipient to initiate the conversation before the bot can message them.

Obtain the user's `chat_id` using Telegram's `getUpdates` API and enter that
chat ID during the Deadline Tracker onboarding screen.

### 5. Run

```bash
streamlit run app.py
```

The app should open at:

`http://localhost:8501`

## Submission checklist

- [ ] Public/shared GitHub repository
- [ ] Live Streamlit Community Cloud URL
- [ ] app.py
- [ ] prompts.py
- [ ] requirements.txt
- [ ] .streamlit/secrets.toml.example
- [ ] .gitignore
- [ ] README.md
- [ ] Real secrets are NOT committed

## Important

AI extraction is an aid, not an authoritative academic calendar.
Always verify important dates against the original document.
