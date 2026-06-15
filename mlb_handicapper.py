from datetime import datetime
from pathlib import Path
import pandas as pd

def main():
    print(f"Running MLB Handicapper - {datetime.now()}")

    output_dir = Path.cwd() / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"mlb_best_bets_{datetime.now().strftime('%Y%m%d')}.csv"

    print(f"Current directory: {Path.cwd()}")
    print(f"Writing CSV to: {output_file}")

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

    print("Found 0 +EV bets")
    print(f"Saved to: {output_file}")
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()
