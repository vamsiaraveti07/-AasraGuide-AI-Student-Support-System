import os
import random
import json

from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "llama-3.1-8b-instant"

TOPICS = {
    "study": ["study", "learn", "syllabus", "notes"],
    "exam": ["exam", "test", "marks", "result", "prepare"],
    "stress": ["stress", "pressure", "overwhelmed", "tired"],
    "coding": ["python", "code", "debug", "error", "logic"],
}

SUGGESTIONS = {
    "study": ["Create study timetable", "Memory tricks", "Explain topic"],
    "exam": ["3-day revision plan", "High-yield topics", "Exam strategy"],
    "stress": ["Breathing exercise", "Relax routine", "Fix workload"],
    "coding": ["Debug code", "Explain logic", "Give example code"],
    "general": ["Tell me more", "Help me plan", "Quick tips"]
}


def detect_topic(text):
    t = text.lower()
    for topic, words in TOPICS.items():
        if any(w in t for w in words):
            return topic
    return "general"


def get_suggestions(topic):
    return random.sample(SUGGESTIONS.get(topic, SUGGESTIONS["general"]), 3)


# ---------------------------------------------------------
# EXAM GUIDE POST-FORMATTING (NEW, FIXED)
# ---------------------------------------------------------

def clean_exam_output(text):
    """
    Fixes AI output to ensure each section is separated
    and bullets are always on new lines.
    """

    # 1. Force new lines before each section header
    SECTION_HEADERS = [
        "IMPORTANT TOPICS",
        "MOST ASKED QUESTIONS",
        "SCORING STRATEGY",
        "EASY SCORING AREAS",
        "STUDY PLAN",
        "EXAM WRITING TIPS"
    ]

    for header in SECTION_HEADERS:
        text = text.replace(header, f"\n{header}\n")

    # 2. Split text into lines
    raw_lines = text.split("\n")
    cleaned_lines = []

    for line in raw_lines:
        l = line.strip()
        if not l:
            continue

        # Convert headings to nice format
        if l.isupper() and len(l.split()) <= 4:
            cleaned_lines.append(f"📌 {l}")
            continue

        # Convert "- " to bullet
        if l.startswith("- "):
            cleaned_lines.append("• " + l[2:])
            continue

        # Convert numbered bullets "1." → bullet
        if re.match(r"^\d+[\.\)] ", l):
            parts = l.split(" ", 1)
            cleaned_lines.append("• " + parts[1])
            continue

        # If it's plain text → convert to bullet
        if not l.startswith("• "):
            cleaned_lines.append("• " + l)
            continue

        cleaned_lines.append(l)

    return "\n".join(cleaned_lines)


# ---------------------------------------------------------
# AI CHAT BULLET GENERATOR
# ---------------------------------------------------------

def format_bullets_clean(text):
    """(kept for chat part) converts raw bullets to clean • bullets"""
    lines = []

    for line in text.split("\n"):
        l = line.strip()

        if not l:
            continue

        if l.startswith("- "):
            l = "• " + l[2:]

        if l.startswith("* "):
            l = "• " + l[2:]

        if not l.startswith("• "):
            l = "• " + l

        lines.append(l)

    return "\n".join(lines)


def generate_ai_reply(history, user_text):
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI student assistant.\n"
                    "STRICT BULLET RULES:\n"
                    "1. Answer ONLY in bullet points.\n"
                    "2. MAX 5 bullets.\n"
                    "3. Each bullet must be short.\n"
                    "4. No paragraphs.\n"
                    "5. No emojis unless user uses them.\n"
                )
            }
        ]

        for m in history:
            messages.append({
                "role": m["role"],
                "content": m["content"]
            })

        messages.append({"role": "user", "content": user_text})

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.3
        )

        bot = response.choices[0].message.content.strip()

        bot_clean = format_bullets_clean(bot)
        topic = detect_topic(user_text)
        suggestions = get_suggestions(topic)

        return bot_clean, suggestions

    except Exception as e:
        print("🔥 AI ERROR:", e)
        return ("• Something went wrong\n• Try again later", ["Try again", "Help me", "Explain more"])


# ---------------------------------------------------------
# EXAM GUIDE GENERATOR (FIXED)
# ---------------------------------------------------------

def generate_exam_helper(subject):
    """Generate structured exam guide using JSON."""
    try:
        print(f"AI Engine: Generating guide for {subject}")

        prompt = f"""
You MUST return ONLY valid JSON.
No markdown. No asterisks. No emojis. No extra text.

Return EXACTLY this structure:

{{
  "IMPORTANT_TOPICS": [
      "topic1", "topic2", "topic3", "topic4", "topic5", "topic6", "topic7"
  ],
  "MOST_ASKED_QUESTIONS": [
      "q1", "q2", "q3", "q4", "q5"
  ],
  "SCORING_STRATEGY": [
      "tip1", "tip2", "tip3", "tip4"
  ],
  "EASY_SCORING_AREAS": [
      "area1", "area2", "area3"
  ],
  "STUDY_PLAN": [
      "step1", "step2", "step3", "step4", "step5"
  ],
  "EXAM_WRITING_TIPS": [
      "tip1", "tip2", "tip3"
  ]
}}

Now generate the exam preparation guide for: {subject}.
Make the content relevant, simple, and exam-focused.
"""

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Return ONLY JSON. No formatting mistakes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )

        raw = response.choices[0].message.content.strip()

        # Remove code fences if model adds them
        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()

        data = json.loads(raw)
        return format_exam_sections(data)

    except Exception as e:
        print("❌ AI Engine Error:", e)
        return "Error generating exam guide."

def format_exam_sections(data):
    """Convert JSON structure into clean ChatGPT-style formatted exam guide."""

    output = []

    SECTION_TITLES = {
        "IMPORTANT_TOPICS": "📌 Important Topics",
        "MOST_ASKED_QUESTIONS": "❓ Most Asked Questions",
        "SCORING_STRATEGY": "🎯 Scoring Strategy",
        "EASY_SCORING_AREAS": "✅ Easy Scoring Areas",
        "STUDY_PLAN": "🗓️ Study Plan",
        "EXAM_WRITING_TIPS": "✍️ Exam Writing Tips"
    }

    for key, items in data.items():
        output.append(f" {SECTION_TITLES[key]}\n")
        for item in items:
            output.append(f"- {item}")
        output.append("")  # blank line

    return "\n".join(output)
