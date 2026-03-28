# Journal Bot

A personal journaling companion powered by Claude. Reflects on your day through gentle conversation, remembers past sessions, tracks your mood over time, and runs as a web app in your browser.

---

## Features

- Warm journaling persona — reflects before asking, one question at a time
- Mood rating (1–5) at the start of each session with colour-coded history
- Conversations saved to `journal.json` with timestamps
- Claude reads your last 3 sessions and references them naturally
- Past entries browsable in the sidebar
- Average mood score for the last 7 days
- Shareable via ngrok for demos
- Also runs as a CLI if you prefer the terminal

---

## Project structure

```
journal_bot/
├── app.py              ← Flask web server
├── journal_bot.py      ← standalone CLI version
├── journal.json        ← created automatically, stores all entries
├── requirements.txt
├── README.md
└── templates/
    └── index.html      ← web UI
```

---

## Requirements

- Python 3.8+
- An Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/journal-bot.git
cd journal-bot

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Add to ~/.zshrc to make it permanent:
# echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc
```

---

## Running the web app

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Running the CLI version

```bash
python journal_bot.py
```

| Command      | What it does                                        |
|--------------|-----------------------------------------------------|
| `summarize`  | Claude writes a journal entry from the conversation |
| `quit`       | Saves the session to journal.json and exits         |

---

## Sharing publicly (temporary)

Use [ngrok](https://ngrok.com) to share a live demo with anyone:

```bash
# Install
brew install ngrok

# Connect your ngrok account (one time)
ngrok config add-authtoken YOUR_TOKEN

# In terminal 1 — run the app
python app.py

# In terminal 2 — expose it
ngrok http 5000
```

ngrok prints a public `https://` URL you can send to anyone. It stays live as long as both terminals are running.

---

## How it works

### Memory

Claude has no built-in memory between sessions. This app gives it continuity by:

1. Saving every session to `journal.json` with a timestamp and mood score
2. On each new session, loading the last 3 entries and injecting them into the system prompt inside `<past_entries>` tags
3. Claude reads these and references them naturally — spotting patterns, following up on themes

### API routes

| Route | Method | What it does |
|-------|--------|--------------|
| `/` | GET | Renders the main UI with sidebar entries |
| `/start` | POST | Begins a session — takes mood, returns Claude's opening message |
| `/chat` | POST | Sends a user message, returns Claude's reply |
| `/save` | POST | Saves the session to journal.json |
| `/entry/<date>` | GET | Returns messages for a past entry |

### Conversation flow

```
User sets mood (1–5)
        ↓
Flask injects mood + last 3 journal entries into system prompt
        ↓
Claude opens the session calibrated to your mood
        ↓
Each message: full history sent to Claude API → reply appended to history
        ↓
"Save & end" → session written to journal.json
```

---

## Customising Claude's persona

Edit the `BASE_SYSTEM` string at the top of `app.py`:

```python
BASE_SYSTEM = """You are a warm, thoughtful journaling companion...
"""
```

Some ideas:

```python
# Stoic coach
"After the user reflects, offer one brief reframe from a stoic perspective."

# Gratitude focused
"Guide the user toward noticing what went well today, even on hard days."

# Structured check-in
"Start each session by asking about work, relationships, and energy levels."
```

---

## Adjusting memory depth

By default the last 3 sessions are loaded. Change this in `build_system_prompt()` in `app.py`:

```python
recent = journal[-3:]  # increase to load more past sessions
```

---

## .gitignore

Add this to avoid committing your journal entries and credentials:

```
venv/
journal.json
.env
__pycache__/
*.pyc
```

---

## requirements.txt

```
anthropic
flask
```

Install with:

```bash
pip install -r requirements.txt
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `AuthenticationError 401` | API key not set — run `echo $ANTHROPIC_API_KEY` to check |
| `Credit balance too low` | Add credits at [console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing) |
| `TemplateNotFound: index.html` | Make sure `index.html` is inside a `templates/` folder next to `app.py` |
| `moodColor is undefined` | Add the `@app.template_global()` function to `app.py` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside your activated venv |
| `externally-managed-environment` | Activate venv first: `source venv/bin/activate` |

---

## Roadmap

- [ ] Streaming responses (word by word)
- [ ] `--review` CLI flag to print past entries
- [ ] Mood chart using saved scores
- [ ] Search across past entries
- [ ] Export entries as markdown or PDF

---

## License

MIT — do whatever you like with this.
