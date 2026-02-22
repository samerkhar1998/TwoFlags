import json
from pathlib import Path


DEFAULT_PROFILE = {
    "username": "Player",
    "level": 1,
    "xp": 0,
    "ratings": {"beginner": 800, "moderate": 800, "hard": 800},
    "stats": {
        "games_vs_ai": 0,
        "wins_vs_ai": 0,
        "losses_vs_ai": 0,
        "win_streak": 0,
        "best_streak": 0,
    },
}

AI_RATINGS = {"beginner": 600, "moderate": 900, "hard": 1200}


class Progression:
    """Single local profile progression manager persisted to data/profile.json."""

    def __init__(self):
        root = Path(__file__).resolve().parent.parent
        self.data_dir = root / "data"
        self.profile_path = self.data_dir / "profile.json"
        self.profile = self.load_profile()

    def load_profile(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.profile_path.exists():
            _write(DEFAULT_PROFILE)
            return _clone(DEFAULT_PROFILE)

        try:
            with self.profile_path.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
        except Exception:
            _write(DEFAULT_PROFILE)
            return _clone(DEFAULT_PROFILE)

        profile = _merge_defaults(loaded, DEFAULT_PROFILE)
        _write(profile)
        return profile

    def save(self):
        _write(self.profile)

    def set_username(self, username):
        username = (username or "").strip()
        if not username:
            username = "Player"
        self.profile["username"] = username
        self.save()

    def current_difficulty_rating(self, difficulty):
        key = _difficulty_key(difficulty)
        return int(self.profile["ratings"].get(key, 800))

    def apply_game_result(self, difficulty, human_won, coach_bonus_points=0):
        """Update XP/level/Elo/stats for one finished Human-vs-AI game."""
        key = _difficulty_key(difficulty)
        if key not in self.profile["ratings"]:
            self.profile["ratings"][key] = 800

        base_xp = 30 if human_won else 10
        coach_bonus = max(-10, min(20, int(coach_bonus_points)))
        xp_gain = max(0, base_xp + coach_bonus)

        self.profile["xp"] += xp_gain
        leveled = 0
        while True:
            needed = next_level_xp(self.profile["level"])
            if self.profile["xp"] < needed:
                break
            self.profile["xp"] -= needed
            self.profile["level"] += 1
            leveled += 1

        old_rating = int(self.profile["ratings"][key])
        opp = AI_RATINGS[key]
        expected = 1.0 / (1.0 + 10 ** ((opp - old_rating) / 400.0))
        score = 1.0 if human_won else 0.0
        new_rating = round(old_rating + 24 * (score - expected))
        self.profile["ratings"][key] = int(new_rating)
        rating_delta = int(new_rating - old_rating)

        stats = self.profile["stats"]
        stats["games_vs_ai"] += 1
        if human_won:
            stats["wins_vs_ai"] += 1
            stats["win_streak"] += 1
            if stats["win_streak"] > stats["best_streak"]:
                stats["best_streak"] = stats["win_streak"]
        else:
            stats["losses_vs_ai"] += 1
            stats["win_streak"] = 0

        self.save()
        return {
            "xp_gain": int(xp_gain),
            "coach_bonus": int(coach_bonus),
            "rating_delta": int(rating_delta),
            "new_rating": int(new_rating),
            "level": int(self.profile["level"]),
            "xp": int(self.profile["xp"]),
            "next_level_xp": int(next_level_xp(self.profile["level"])),
            "win_streak": int(stats["win_streak"]),
            "best_streak": int(stats["best_streak"]),
            "leveled": int(leveled),
        }


def next_level_xp(level):
    return 100 + (max(1, int(level)) - 1) * 25


def _difficulty_key(difficulty):
    if isinstance(difficulty, str):
        key = difficulty.strip().lower()
        if key in ("beginner", "moderate", "hard"):
            return key
    return "moderate"


def _merge_defaults(obj, default):
    if not isinstance(obj, dict):
        return _clone(default)
    merged = _clone(default)
    for k, v in obj.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = _merge_defaults(v, merged[k])
        else:
            merged[k] = v
    return merged


def _clone(value):
    return json.loads(json.dumps(value))


def _write(profile):
    path = Path(__file__).resolve().parent.parent / "data" / "profile.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
