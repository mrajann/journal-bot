import anthropic
import json
import os
from datetime import datetime

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

JOURNAL_FILE = "journal.json"

BASE_SYSTEM = """You are a warm, thoughtful journaling companion.

Your role is to help the user reflect on their day, feelings, and experiences
through gentle conversation — not to give advice unless asked.

Guidelines:
- Ask one open-ended question at a time, never a list of questions
- Reflect back what you hear before asking anything new
- Notice emotional themes and name them gently ("it sounds like you're carrying a lot today")
- If the user seems done, offer to summarize the session as a journal entry
- Keep responses concise — 2-4 sentences max unless summarizing
- When the user types 'summarize', write a short, warm journal entry in second person
  capturing the themes and feelings from this conversation
"""


# ── Journal file helpers ──────────────────────────────────────────────────────

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
    print("\n[Entry saved to journal.json]")


# ── System prompt with memory ─────────────────────────────────────────────────

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
        user_lines = [m["content"] for m in entry["messages"] if m["role"] == "user"]
        # Strip the auto-inserted mood line from display
        user_lines = [l for l in user_lines if not l.startswith("[Mood:")]
        history_text += f"\n[{date}{mood_str}]\n" + "\n".join(user_lines) + "\n"

    return BASE_SYSTEM + f"""
You have access to the user's recent journal entries:
<past_entries>
{history_text.strip()}
</past_entries>

Reference these naturally when relevant — notice patterns, growth, recurring themes.
Do not bring them up robotically; only mention them when it genuinely adds to the conversation.
"""


# ── Mood input ────────────────────────────────────────────────────────────────

def get_mood():
    labels = {1: "rough", 2: "low", 3: "okay", 4: "good", 5: "great"}
    print("\nHow are you feeling today?")
    for n, label in labels.items():
        print(f"  {n} — {label}")
    while True:
        val = input("Your mood (1–5): ").strip()
        if val in ("1", "2", "3", "4", "5"):
            n = int(val)
            print(f"\nGot it — {labels[n]}. Let's begin.\n")
            return n
        print("Please enter a number between 1 and 5.")


# ── Main chat loop ────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  Your Journal")
    print("  Type 'summarize' to get a journal entry")
    print("  Type 'quit' to save and exit")
    print("=" * 50)

    mood = get_mood()
    system = build_system_prompt()
    history = []

    # Seed the conversation with mood context (Claude sees this, feels natural)
    history.append({
        "role": "user",
        "content": f"[Mood: {mood}/5] Starting my journal for today.",
    })

    # Claude opens the session
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=system,
        messages=history,
    )
    opening = response.content[0].text
    history.append({"role": "assistant", "content": opening})
    print(f"Claude: {opening}\n")

    # Conversation loop
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            save_entry(history, mood)
            print("Take care. See you next time.\n")
            break

        history.append({"role": "user", "content": user_input})

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=history,
        )
        reply = response.content[0].text
        history.append({"role": "assistant", "content": reply})
        print(f"\nClaude: {reply}\n")


if __name__ == "__main__":
    main()
