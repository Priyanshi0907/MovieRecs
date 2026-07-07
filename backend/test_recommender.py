import sys
import os
from dotenv import load_dotenv
load_dotenv()

# Add the backend directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models import Movie, Rating, User
from app.seed import seed_database
from app.recommender import train_recommender, get_similar_movies, get_hybrid_recommendations
from app.ai import generate_ai_summary, generate_ai_review_analysis, handle_chatbot_query

def main():
    print("=== STARTING RECOMMENDATION SYSTEM VERIFICATION ===")
    
    # 1. Initialize DB and Seed
    print("\n1. Seeding database...")
    try:
        seed_database()
        db = SessionLocal()
        movies_count = db.query(Movie).count()
        users_count = db.query(User).count()
        ratings_count = db.query(Rating).count()
        print(f"Database seeded. Movies: {movies_count}, Users: {users_count}, Ratings: {ratings_count}")
        assert movies_count > 100, "Should seed at least 100 movies"
        assert users_count > 50, "Should seed at least 50 users"
        assert ratings_count > 1000, "Should seed at least 1000 ratings"
        
        # 2. Train Recommender
        print("\n2. Training Recommender Models...")
        train_recommender(db)
        
        # 3. Test Content-Based similar movies
        print("\n3. Testing Content-Based similarity for 'Interstellar'...")
        interstellar = db.query(Movie).filter(Movie.title == "Interstellar").first()
        if interstellar:
            similar = get_similar_movies(interstellar.id, db, limit=5)
            print("Movies similar to 'Interstellar' (Content-Based):")
            for m in similar:
                print(f"  - {m.title} (Genres: {m.genres}, Director: {m.director})")
            assert len(similar) > 0, "Should return similar movies"
        else:
            print("ERROR: Interstellar not found in seeded database")
            
        # 4. Test Hybrid Recommendations
        print("\n4. Testing Hybrid Recommendations for Admin User...")
        admin = db.query(User).filter(User.email == "priv0907@gmail.com").first()
        if admin:
            hybrid_recs = get_hybrid_recommendations(admin.id, db, limit=5)
            print("Hybrid recommendations (Collaborative SVD + Content Similarity):")
            for m in hybrid_recs:
                print(f"  - {m.title} (Genres: {m.genres}, Director: {m.director}, Rating: {m.vote_average})")
            assert len(hybrid_recs) > 0, "Should return hybrid recommendations"
            
        # 5. Test AI features (Fallback mode)
        print("\n5. Testing AI Features (Fallback)...")
        if interstellar:
            summary = generate_ai_summary(interstellar.title, interstellar.overview)
            print(f"AI Summary Hook: {summary}")
            assert len(summary) > 0
            
            reviews = generate_ai_review_analysis(interstellar.title, interstellar.genres, interstellar.director)
            print(f"AI Review Analysis: {reviews}")
            assert "audience_opinion" in reviews
            assert "tone" in reviews

        # 6. Test Chatbot Query
        print("\n6. Testing AI Chatbot Query...")
        chat_resp = handle_chatbot_query("I want a sci-fi movie like Interstellar but less emotional", db)
        print(f"User Query: 'I want a sci-fi movie like Interstellar but less emotional'")
        print(f"Chatbot response: {chat_resp['message']}")
        print("Chatbot recommendations:")
        for m in chat_resp["movies"]:
            print(f"  - {m['title']} ({m['vote_average']} star)")
        assert len(chat_resp["movies"]) > 0

        print("\n=== ALL VERIFICATION CHECKS PASSED SUCCESSFULLY ===")
    except Exception as e:
        print(f"\nVerification Failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
