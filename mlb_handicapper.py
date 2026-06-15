import os
from datetime import datetime
from pathlib import Path
import requests
import pandas as pd

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "YOUR_ODDS_API_KEY_HERE")

def get_mlb_odds():
    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h,totals",
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
market_name = ""
pick_text = ""

for bm in bookmakers:
    bm_name = bm.get("title", "")
    markets = bm.get("markets", [])
    for market in markets:
        if market.get("key") in ["h2h", "totals"]:
            market_name = market.get("key")
            outcomes = market.get("outcomes", [])
            if market_name == "h2h" and len(outcomes) >= 2:
                odds_text = f"{outcomes[0].get('name')} {outcomes[0].get('price')}, {outcomes[1].get('name')} {outcomes[1].get('price')}"
                pick_text = "TBD"
                break
            if market_name == "totals" and len(outcomes) >= 2:
                odds_text = f"Over {outcomes[0].get('price')}, Under {outcomes[1].get('price')}"
                pick_text = "TBD"
                break
    if odds_text:
        break

row = {
    "date": commence[:10] if commence else datetime.now().strftime("%Y-%m-%d"),
    "game": f"{away} @ {home}",
    "market": market_name if market_name else "H2H/Totals",
    "pick": pick_text if pick_text else "TBD",
    "odds": odds_text if odds_text else "No odds found",
    "stake": 1.0,
    "proj_edge": 0.0,
    "result": "pending",
    "clv": 0.0,
    "notes": f"bookmakers={len(bookmakers)}"
}
        }
        rows.append(row)

    if not rows:
        rows = [{
            "date": datetime.now().strftime("%Y-%m-%d"),
            "game": "TEST GAME",
            "market": "Total",
            "pick": "Over",
            "odds": -110,
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
