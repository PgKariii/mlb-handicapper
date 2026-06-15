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

        odds_text = ""
        pick_text = "TBD"
        best_odds = None
        best_name = None
        pick_prob = None

        for bm in bookmakers:
            for market in bm.get("markets", []):
                if market.get("key") == "h2h":
                    outcomes = market.get("outcomes", [])
                    if len(outcomes) >= 2:
                        a = outcomes[0]
                        b = outcomes[1]

                        odds_text = f"{a.get('name')} {a.get('price')}, {b.get('name')} {b.get('price')}"

                        if a.get("price", 0) > b.get("price", 0):
                            best_name = a.get("name")
                            best_odds = a.get("price")
                        else:
                            best_name = b.get("name")
                            best_odds = b.get("price")

                        pick_text = best_name
                        pick_prob = round(implied_probability(best_odds), 3)
                        break
            if odds_text:
                break

        row = {
            "date": commence[:10] if commence else datetime.now().strftime("%Y-%m-%d"),
            "game": f"{away} @ {home}",
            "market": "h2h",
            "pick": pick_text,
            "odds": odds_text if odds_text else "No odds found",
            "stake": 1.0,
            "proj_edge": 0.0,
            "result": "pending",
            "clv": 0.0,
            "notes": f"bookmakers={len(bookmakers)}, pick_prob={pick_prob if pick_prob is not None else 'NA'}"
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
