import json
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
import anthropic

app = Flask(__name__)
@app.template_global()
def moodColor(mood):
    if not mood:
        return '#ccc'
    if mood <= 2:
        return '#E24B4A'
    if mood == 3:
        return '#EF9F27'
    return '#1D9E75'
app.secret_key = "journal-secret-key-change-me"

client = anthropic.Anthropic()
JOURNAL_FILE = "journal.json"

BASE_SYSTEM = """You are a warm, thoughtful journaling companion.

Your role is to help the user reflect on their day, feelings, and experiences
through gentle conversation — not to give advice unless asked.

Guidelines:
- Ask one open-ended question at a time, never a list of questions
- Reflect back what you hear before asking anything new
- Notice emotional themes and name them gently
- Keep responses concise — 2-4 sentences max unless summarizing
- When the user asks to summarize, write a short warm journal entry in second person
  capturing the themes and feelings from this conversation
"""


# ── Journal helpers ───────────────────────────────────────────────────────────

def load_journal():
    if os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE) as f:
            return json.load(f)
    return []


def save_entry(messages, mood):
    journal = load_journal()
    journal.append({
        "date": datetime.now().isoformat(),
        "mood": mood,
        "messages": messages,
    })
    with open(JOURNAL_FILE, "w") as f:
        json.dump(journal, f, indent=2)


def build_system_prompt():
    journal = load_journal()
    if not journal:
        return BASE_SYSTEM

    recent = journal[-3:]
    history_text = ""
    for entry in recent:
        date = entry["date"][:10]
        mood = entry.get("mood")
        mood_str = f" | Mood: {mood}/5" if mood else ""
        user_lines = [
            m["content"] for m in entry["messages"]
            if m["role"] == "user" and not m["content"].startswith("[Mood:")
        ]
        history_text += f"\n[{date}{mood_str}]\n" + "\n".join(user_lines) + "\n"

    return BASE_SYSTEM + f"""
You have access to the user's recent journal entries:
<past_entries>
{history_text.strip()}
</past_entries>

Reference these naturally when relevant — notice patterns, growth, recurring themes.
Only mention past entries when it genuinely adds to the conversation.
"""


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    journal = load_journal()
    entries = []
    for e in reversed(journal):
        entries.append({
            "date": e["date"][:10],
            "mood": e.get("mood"),
        })
    avg_mood = None
    recent_moods = [e.get("mood") for e in journal[-7:] if e.get("mood")]
    if recent_moods:
        avg_mood = round(sum(recent_moods) / len(recent_moods), 1)

    return render_template("index.html", entries=entries, avg_mood=avg_mood)


@app.route("/start", methods=["POST"])
def start():
    """Begin a new session — set mood, get Claude's opening message."""
    mood = int(request.json.get("mood", 3))
    session["mood"] = mood
    session["history"] = [
        {"role": "user", "content": f"[Mood: {mood}/5] Starting my journal for today."}
    ]

    system = build_system_prompt()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=system,
        messages=session["history"],
    )
    reply = response.content[0].text
    session["history"].append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})


@app.route("/chat", methods=["POST"])
def chat():
    """Send a user message, get Claude's reply."""
    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "empty message"}), 400

    history = session.get("history", [])
    history.append({"role": "user", "content": user_message})

    system = build_system_prompt()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=history,
    )
    reply = response.content[0].text
    history.append({"role": "assistant", "content": reply})
    session["history"] = history

    return jsonify({"reply": reply})


@app.route("/save", methods=["POST"])
def save():
    """Save the current session to journal.json."""
    history = session.get("history", [])
    mood = session.get("mood", 3)
    if history:
        save_entry(history, mood)
        session.clear()
    return jsonify({"saved": True})


@app.route("/entry/<date>")
def get_entry(date):
    """Return messages for a past entry by date."""
    journal = load_journal()
    for entry in reversed(journal):
        if entry["date"][:10] == date:
            messages = [
                m for m in entry["messages"]
                if not m["content"].startswith("[Mood:")
            ]
            return jsonify({
                "date": entry["date"][:10],
                "mood": entry.get("mood"),
                "messages": messages,
            })
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)
