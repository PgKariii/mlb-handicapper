from datetime import datetime
from pathlib import Path
import requests
import pandas as pd
import os
import math

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "YOUR_ODDS_API_KEY_HERE")

def implied_probability(odds):
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    return 100 / (odds + 100)

def fair_probabilities(p1, p2):
    total = p1 + p2
    if total == 0:
        return 0, 0
    return p1 / total, p2 / total

def expected_value_per_unit(prob, odds):
    if odds < 0:
        profit = 100 / abs(odds)
    else:
        profit = odds / 100
    return prob * profit - (1 - prob)

def get_mlb_odds():
    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "american"
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Odds fetch error: {e}")
        return []

def normalize_team(name):
    return (name or "").strip().lower()

def starter_strength(team_name, probable_pitcher=None):
    return 0.00

def bullpen_strength(team_name):
    return 0.00

def lineup_strength(team_name, lineup=None):
    return 0.00

def park_factor_adjustment(home_team=None, park_name=None):
    return 0.00

def weather_adjustment(temp_f=None, wind_mph=None, humidity=None):
    adj = 0.00
    if temp_f is not None:
        if temp_f >= 85:
            adj += 0.01
        elif temp_f <= 55:
            adj -= 0.01
    if wind_mph is not None:
        if wind_mph >= 12:
            adj += 0.005
    return adj

def home_field_adjustment(is_home):
    return 0.02 if is_home else 0.00

def run_environment_score(team_name, is_home, home_team):
    score = 0.50
    score += starter_strength(team_name)
    score += bullpen_strength(team_name)
    score += lineup_strength(team_name)
    score += home_field_adjustment(is_home)
    score += park_factor_adjustment(home_team if is_home else None)
    score += weather_adjustment()
    return max(0.01, min(0.99, score))

def win_probability_from_score(score):
    return max(0.01, min(0.99, score))

def main():
    print(f"Running MLB Handicapper - {datetime.now()}")

    output_dir = Path.cwd() / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"mlb_best_bets_{datetime.now().strftime('%Y%m%d')}.csv"

    print(f"Current directory: {Path.cwd()}")
    print(f"Writing CSV to: {output_file}")

    games = get_mlb_odds()
    rows = []

    for game in games:
        home = game.get("home_team", "Unknown")
        away = game.get("away_team", "Unknown")
        commence = game.get("commence_time", "")
        bookmakers = game.get("bookmakers", [])

        best_market = None
        best_book = None

        for bm in bookmakers:
            for market in bm.get("markets", []):
                if market.get("key") == "h2h":
                    outcomes = market.get("outcomes", [])
                    if len(outcomes) >= 2:
                        best_market = outcomes
                        best_book = bm.get("title", "")
                        break
            if best_market:
                break

        if not best_market or len(best_market) < 2:
            continue

        game_rows = []
        for outcome in best_market:
            team_name = outcome.get("name", "")
            team_odds = outcome.get("price", 0)
            book_prob = implied_probability(team_odds)
            is_home = normalize_team(team_name) == normalize_team(home)

            score = run_environment_score(team_name, is_home, home)
            model_prob = win_probability_from_score(score)
            ev = expected_value_per_unit(model_prob, team_odds)
            edge = model_prob - book_prob

            game_rows.append({
                "date": commence[:10] if commence else datetime.now().strftime("%Y-%m-%d"),
                "game": f"{away} @ {home}",
                "market": "h2h",
                "team": team_name,
                "odds": team_odds,
                "stake": 1.0,
                "model_prob": round(model_prob, 3),
                "book_prob": round(book_prob, 3),
                "proj_edge": round(edge * 100, 2),
                "ev": round(ev, 4),
                "result": "+EV" if ev > 0 else "skip",
                "clv": 0.0,
                "notes": f"book={best_book}"
            })

        rows.extend([r for r in game_rows if r["ev"] > 0])

    if not rows:
        rows = [{
            "date": datetime.now().strftime("%Y-%m-%d"),
            "game": "TEST GAME",
            "market": "h2h",
            "team": "TBD",
            "odds": "No +EV rows",
            "stake": 1.0,
            "model_prob": 0.5,
            "book_prob": 0.5,
            "proj_edge": 0.0,
            "ev": 0.0,
            "result": "pending",
            "clv": 0.0,
            "notes": "fallback row because no +EV bets were found"
        }]

    df = pd.DataFrame(rows)
    df.to_csv(output_file, index=False)

    print(f"Found {len(rows)} rows")
    print(f"Saved to: {output_file}")
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()
