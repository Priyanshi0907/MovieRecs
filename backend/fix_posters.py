import os
from dotenv import load_dotenv
from app.database import SessionLocal
from app.tmdb import backfill_missing_posters, repair_broken_posters

def main():
    load_dotenv()
    api_key = os.getenv("TMDB_API_KEY", "")
    if not api_key:
        print("TMDB_API_KEY is not set.")
        return

    db = SessionLocal()
    try:
        print("Starting backfill for missing posters...")
        backfill_res = backfill_missing_posters(db, api_key)
        print("Backfill result:", backfill_res)
        
        print("\nStarting repair for broken posters...")
        repair_res = repair_broken_posters(db, api_key)
        print("Repair result:", repair_res)
    finally:
        db.close()

if __name__ == "__main__":
    main()
