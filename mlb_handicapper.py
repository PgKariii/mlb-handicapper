from datetime import datetime
from pathlib import Path
import requests
import pandas as pd
import os

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

        best_book = None
        best_market = None

        for bm in bookmakers:
            for market in bm.get("markets", []):
                if market.get("key") == "h2h":
                    outcomes = market.get("outcomes", [])
                    if len(outcomes) >= 2:
                        best_book = bm.get("title", "")
                        best_market = outcomes
                        break
            if best_market:
                break

        if best_market and len(best_market) >= 2:
            a = best_market[0]
            b = best_market[1]

            a_name = a.get("name", "")
            b_name = b.get("name", "")
            a_odds = a.get("price", 0)
            b_odds = b.get("price", 0)

            a_imp = implied_probability(a_odds)
            b_imp = implied_probability(b_odds)
            a_fair, b_fair = fair_probabilities(a_imp, b_imp)

            if a_imp < b_imp:
                pick_name = a_name
                pick_odds = a_odds
                fair_prob = a_fair
                book_prob = a_imp
            else:
                pick_name = b_name
                pick_odds = b_odds
                fair_prob = b_fair
                book_prob = b_imp

            ev = expected_value_per_unit(fair_prob, pick_odds)

            row = {
                "date": commence[:10] if commence else datetime.now().strftime("%Y-%m-%d"),
                "game": f"{away} @ {home}",
                "market": "h2h",
                "pick": pick_name,
                "odds": pick_odds,
                "stake": 1.0,
                "proj_edge": round((fair_prob - book_prob) * 100, 2),
                "result": "+EV" if ev > 0 else "-EV",
                "clv": 0.0,
                "notes": f"book={best_book}, fair_prob={round(fair_prob, 3)}, book_prob={round(book_prob, 3)}, ev={round(ev, 4)}"
            }
            rows.append(row)

    if not rows:
        rows = [{
            "date": datetime.now().strftime("%Y-%m-%d"),
            "game": "TEST GAME",
            "market": "h2h",
            "pick": "TBD",
            "odds": "No games returned",
            "stake": 1.0,
            "proj_edge": 0.0,
            "result": "pending",
            "clv": 0.0,
            "notes": "fallback row because no games were returned"
        }]

    df = pd.DataFrame(rows)
    df.to_csv(output_file, index=False)

    print(f"Found {len(rows)} rows")
    print(f"Saved to: {output_file}")
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()
