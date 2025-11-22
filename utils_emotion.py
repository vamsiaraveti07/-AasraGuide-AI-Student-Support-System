def detect_emotion(text):
    t = (text or "").lower()

    crisis_phrases = [
        "i want to die", "kill myself", "suicide", "i'll kill myself", "i can't go on"
    ]
    for p in crisis_phrases:
        if p in t:
            return "crisis", 1.0, True

    # Simple keyword-based emotion
    if any(w in t for w in ["stressed", "stress", "overwhelmed", "pressure"]):
        return "stressed", 0.85, False
    if any(w in t for w in ["anxious", "anxiety", "panic", "worried"]):
        return "anxious", 0.8, False
    if any(w in t for w in ["sad", "depressed", "unhappy", "down"]):
        return "sad", 0.8, False
    if any(w in t for w in ["angry", "mad", "furious"]):
        return "angry", 0.8, False
    if any(w in t for w in ["alone", "lonely", "isolated"]):
        return "lonely", 0.75, False
    if any(w in t for w in ["happy", "great", "good", "awesome"]):
        return "happy", 0.9, False

    # fallback neutral
    return "neutral", 0.5, False
