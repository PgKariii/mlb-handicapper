"""
MLB Auto-Updating Handicapper
"""

import requests
import pandas as pd
from datetime import datetime
import os
from pathlib import Path

# API Key (will be set in GitHub secrets later)
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "YOUR_ODDS_API_KEY_HERE")

# Settings
MIN_EDGE_THRESHOLD = 0.02  # 2% minimum edge

def get_mlb_odds(date):
    """Fetch MLB odds"""
    url = "https://api.the-odds-api.com/v4/sports/mlb/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "date": date,
        "markets": "h2h,totals",
        "regions": "us"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_pitcher_profile(team):
    """Get starter stats (simplified)"""
    return {
        "xfip": 3.95,
        "recent_pitches": 95
    }

def get_bullpen_usage(team):
    """Get bullpen usage (simplified)"""
    return {
        "innings_1d": 1.2,
        "innings_3d": 2.8
    }

class MLBHandicapper:
    def __init__(self):
        self.min_edge = MIN_EDGE_THRESHOLD
    
    def find_best_bets(self):
        """Find +EV bets"""
        date = datetime.now().strftime("%Y-%m-%d")
        games = get_mlb_odds(date)
        
        best_bets = []
        
        for game in games:
            away = game.get("team_name", "Unknown")
            home = game.get("home_team", "Unknown")
            
            away_sp = get_pitcher_profile(away)
            home_sp = get_pitcher_profile(home)
            away_bullpen = get_bullpen_usage(away)
            home_bullpen = get_bullpen_usage(home)
            
            # Estimate runs
            away_runs = 4.2 + (4.0 - away_sp["xfip"]) * 0.3
            home_runs = 4.2 + (4.0 - home_sp["xfip"]) * 0.3
            
            projected_total = away_runs + home_runs
            
            # Get market total
            markets = game.get("markets", [])
            totals = None
            for m in markets:
                if m.get("key") == "totals":
                    totals = m
                    break
            
            if totals:
                outlet = totals.get("outlets", [{}])[0]
                asks = outlet.get("asks", [])
                if len(asks) >= 2:
                    market_total = (asks[0].get("price", 0) + asks[1].get("price", 0)) / 2
                    over_price = asks[0].get("price", -110)
                else:
                    continue
            else:
                continue
            
            # Calculate edge
            edge = (projected_total - market_total) / market_total
            
            if abs(edge) >= self.min_edge:
                best_bets.append({
                    "date": date,
                    "game": f"{away} @ {home}",
                    "market": "Total",
                    "pick": "Over" if edge > 0 else "Under",
                    "odds": over_price,
                    "stake": 1.0,
                    "proj_edge": round(edge * 100, 2),
                    "result": "pending",
                    "clv": 0.0,
                    "notes": f"Fatigue check: Away={away_bullpen['innings_1d']}, Home={home_bullpen['innings_1d']}"
                })
        
        return best_bets

def main():
    print(f"Running MLB Handicapper - {datetime.now()}")
    
    handicapper = MLBHandicapper()
    best_bets = handicapper.find_best_bets()
    
    output_file = f"output/mlb_best_bets_{datetime.now().strftime('%Y%m%d')}.csv"
    Path("output").mkdir(exist_ok=True)
    
    if best_bets:
        df = pd.DataFrame(best_bets)
    else:
        df = pd.DataFrame([{
            "date": datetime.now().strftime("%Y-%m-%d"),
            "game": "TEST GAME",
            "market": "Total",
            "pick": "Over",
            "odds": -110,
            "stake": 1.0,
            "proj_edge": 0.0,
            "result": "pending",
            "clv": 0.0,
            "notes": "test row so CSV is not empty"
        }])
    
    df.to_csv(output_file, index=False)
    
    print(f"Found {len(best_bets)} +EV bets")
    print(f"Saved to: {output_file}")
    print(df.to_string(index=False))
