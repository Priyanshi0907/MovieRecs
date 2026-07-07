import random
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from .models import Movie, User, Rating, Watchlist, History, Review
from .auth import get_password_hash

def seed_database():
    db = SessionLocal()
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    # Clear old data safely (avoids SQLite database lock errors while uvicorn is running)
    try:
        db.query(Rating).delete()
        db.query(Watchlist).delete()
        db.query(History).delete()
        db.query(Review).delete()
        db.query(User).delete()
        db.query(Movie).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning: safe delete cleanup failed, attempting recreation: {e}")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    print("Seeding movies...")

    # Real movies data (45 popular movies)
    real_movies = [
        # Sci-Fi & Space
        {
            "title": "Interstellar",
            "genres": ["Sci-Fi", "Adventure", "Drama"],
            "overview": "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
            "cast": ["Matthew McConaughey", "Anne Hathaway", "Jessica Chastain", "Michael Caine"],
            "director": "Christopher Nolan",
            "poster_path": "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
            "backdrop_path": "/xJHokZbljvjCNmzb04z2tHNi65e.jpg",
            "runtime": 169,
            "vote_average": 8.4,
            "popularity": 185.4,
            "release_date": "2014-11-07",
            "budget": 165000000,
            "revenue": 701729206,
            "youtube_trailer_id": "zSWdZVtXT7U",
            "streaming_platforms": ["Netflix", "Paramount+", "Prime Video"],
            "languages": ["English"],
            "awards": ["Oscar Winner (Best Visual Effects)", "BAFTA Winner"],
            "country": "United States"
        },
        {
            "title": "Inception",
            "genres": ["Sci-Fi", "Action", "Thriller"],
            "overview": "Cobb, a skilled thief who steals valuable secrets from deep within the subconscious during the dream state, is offered a chance to have his history erased as payment for a seemingly impossible task: \"inception\", the implantation of another person's idea into their subconscious.",
            "cast": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Elliot Page", "Tom Hardy"],
            "director": "Christopher Nolan",
            "poster_path": "/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg",
            "backdrop_path": "/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg",
            "runtime": 148,
            "vote_average": 8.3,
            "popularity": 142.2,
            "release_date": "2010-07-16",
            "budget": 160000000,
            "revenue": 825532764,
            "youtube_trailer_id": "YoHD9XEInc0",
            "streaming_platforms": ["Netflix", "Max"],
            "languages": ["English", "Japanese"],
            "awards": ["4 Oscars (Cinematography, Sound Editing, Sound Mixing, Visual Effects)"],
            "country": "United States"
        },
        {
            "title": "The Dark Knight",
            "genres": ["Action", "Crime", "Drama"],
            "overview": "Batman raises the stakes in his war on crime. With the help of Lt. Jim Gordon and District Attorney Harvey Dent, Batman sets out to dismantle the remaining criminal organizations that plague the streets. The partnership proves to be effective, but they soon find themselves prey to a reign of chaos unleashed by a rising criminal mastermind known to the terrified citizens of Gotham as the Joker.",
            "cast": ["Christian Bale", "Heath Ledger", "Aaron Eckhart", "Maggie Gyllenhaal"],
            "director": "Christopher Nolan",
            "poster_path": "/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
            "backdrop_path": "/nMKdUUepR0i5zn0y1T4CsSB5chy.jpg",
            "runtime": 152,
            "vote_average": 8.5,
            "popularity": 190.5,
            "release_date": "2008-07-18",
            "budget": 185000000,
            "revenue": 1004558444,
            "youtube_trailer_id": "EXeTwQWrcwY",
            "streaming_platforms": ["Max", "Peacock"],
            "languages": ["English"],
            "awards": ["2 Oscars (Supporting Actor Heath Ledger, Sound Editing)"],
            "country": "United States"
        },
        {
            "title": "The Martian",
            "genres": ["Sci-Fi", "Adventure", "Drama"],
            "overview": "During a manned mission to Mars, Astronaut Mark Watney is presumed dead after a fierce storm and left behind by his crew. But Watney has survived and finds himself stranded and alone on the hostile planet. With only meager supplies, he must draw upon his ingenuity, wit and spirit to subsist and find a way to signal to Earth that he is alive.",
            "cast": ["Matt Damon", "Jessica Chastain", "Kristen Wiig", "Jeff Daniels"],
            "director": "Ridley Scott",
            "poster_path": "/5aGHa5X2mSOXXt2nQ6i42886n0V.jpg",
            "backdrop_path": "/j976sb7tPXuB6v2UjqpvUiLvgoY.jpg",
            "runtime": 144,
            "vote_average": 7.7,
            "popularity": 98.4,
            "release_date": "2015-10-02",
            "budget": 108000000,
            "revenue": 630161890,
            "youtube_trailer_id": "ej3ioOneTy8",
            "streaming_platforms": ["Hulu", "Disney+"],
            "languages": ["English"],
            "awards": ["Golden Globe Winner (Best Motion Picture - Comedy or Musical)"],
            "country": "United States"
        },
        {
            "title": "Arrival",
            "genres": ["Sci-Fi", "Drama", "Mystery"],
            "overview": "Taking place after mysterious spacecraft touch down across the globe, an elite team, led by expert linguist Louise Banks, is brought together to investigate. As mankind teeters on the verge of global war, Banks and the crew race against time for answers.",
            "cast": ["Amy Adams", "Jeremy Renner", "Forest Whitaker", "Michael Stuhlbarg"],
            "director": "Denis Villeneuve",
            "poster_path": "/48gHmRBR14xSpOI77275FW27QOm.jpg",
            "backdrop_path": "/y2Y474o5n24XGUE58Z5v7nnTy96.jpg",
            "runtime": 116,
            "vote_average": 7.6,
            "popularity": 64.3,
            "release_date": "2016-11-11",
            "budget": 47000000,
            "revenue": 203388186,
            "youtube_trailer_id": "tFMo3wCIAtU",
            "streaming_platforms": ["Paramount+", "Pluto TV"],
            "languages": ["English", "Russian", "Mandarin"],
            "awards": ["Oscar Winner (Best Sound Editing)"],
            "country": "United States"
        },
        # Crime & Thriller
        {
            "title": "Pulp Fiction",
            "genres": ["Crime", "Thriller"],
            "overview": "A burger-loving hitman, his philosophical partner, a drug-addled gangster's moll, and a washed-up boxer converge in this sprawling, comedic crime caper. Their adventures unfurl in three stories that ingeniously trip back and forth in time.",
            "cast": ["John Travolta", "Samuel L. Jackson", "Uma Thurman", "Bruce Willis"],
            "director": "Quentin Tarantino",
            "poster_path": "/suaEOtk1N1sgg2MTM7oZd2cfVp3.jpg",
            "backdrop_path": "/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",
            "runtime": 154,
            "vote_average": 8.5,
            "popularity": 110.4,
            "release_date": "1994-10-14",
            "budget": 8000000,
            "revenue": 213928762,
            "youtube_trailer_id": "s7Egux54A4A",
            "streaming_platforms": ["Max", "Paramount+"],
            "languages": ["English", "Spanish"],
            "awards": ["Oscar Winner (Best Original Screenplay)", "Palme d'Or Winner"],
            "country": "United States"
        },
        {
            "title": "Django Unchained",
            "genres": ["Drama", "Action", "Western"],
            "overview": "With the help of a German bounty hunter, a freed slave sets out to rescue his wife from a brutal Mississippi plantation owner.",
            "cast": ["Jamie Foxx", "Christoph Waltz", "Leonardo DiCaprio", "Kerry Washington"],
            "director": "Quentin Tarantino",
            "poster_path": "/7oWY853Zhk8nLU43jZszuB6CXj1.jpg",
            "backdrop_path": "/2oZhyved3jZQq7wjoi7QjOdhb6x.jpg",
            "runtime": 165,
            "vote_average": 8.2,
            "popularity": 118.5,
            "release_date": "2012-12-25",
            "budget": 100000000,
            "revenue": 425368238,
            "youtube_trailer_id": "0fUCuvNlOCg",
            "streaming_platforms": ["Hulu", "Starz"],
            "languages": ["English", "German", "French"],
            "awards": ["2 Oscars (Best Original Screenplay, Supporting Actor Christoph Waltz)"],
            "country": "United States"
        },
        {
            "title": "Fight Club",
            "genres": ["Drama", "Thriller"],
            "overview": "A ticking-time-bomb insomniac and a slippery soap salesman channel male aggression into a shocking new form of therapy. Their concept catches on, with underground \"fight clubs\" forming in every town, until an eccentric gets in the way and ignites an out-of-control spiral toward oblivion.",
            "cast": ["Edward Norton", "Brad Pitt", "Helena Bonham Carter", "Jared Leto"],
            "director": "David Fincher",
            "poster_path": "/pB8BM7pdSp6B66W0Z7097GbbFM5.jpg",
            "backdrop_path": "/fCayjUz2EQ1qq687lruY6wH614u.jpg",
            "runtime": 139,
            "vote_average": 8.4,
            "popularity": 92.4,
            "release_date": "1999-10-15",
            "budget": 63000000,
            "revenue": 100853753,
            "youtube_trailer_id": "O1tVdGpJyOo",
            "streaming_platforms": ["Hulu", "Prime Video"],
            "languages": ["English"],
            "awards": ["Oscar Nominated"],
            "country": "United States"
        },
        {
            "title": "Shutter Island",
            "genres": ["Thriller", "Mystery", "Drama"],
            "overview": "In 1954, a U.S. Marshal investigates the disappearance of a murderer who escaped from a hospital for the criminally insane on Shutter Island.",
            "cast": ["Leonardo DiCaprio", "Mark Ruffalo", "Ben Kingsley", "Michelle Williams"],
            "director": "Martin Scorsese",
            "poster_path": "/kve201gZzXmZpxCVRzVP1qg17Cc.jpg",
            "backdrop_path": "/539m73Z5U0j1uC85r5i8344s2h1.jpg",
            "runtime": 138,
            "vote_average": 8.2,
            "popularity": 89.2,
            "release_date": "2010-02-19",
            "budget": 80000000,
            "revenue": 294803014,
            "youtube_trailer_id": "5iaYLCip5Qk",
            "streaming_platforms": ["Netflix", "Paramount+"],
            "languages": ["English"],
            "awards": ["National Board of Review Winner"],
            "country": "United States"
        },
        {
            "title": "The Wolf of Wall Street",
            "genres": ["Comedy", "Crime", "Drama"],
            "overview": "A New York stockbroker refuses to cooperate in a large securities fraud case involving corruption on Wall Street, corporate banking world and mob infiltration. Based on Jordan Belfort's autobiography.",
            "cast": ["Leonardo DiCaprio", "Jonah Hill", "Margot Robbie", "Matthew McConaughey"],
            "director": "Martin Scorsese",
            "poster_path": "/jwwxzIY90S6Uo2S70d7Sj0a5r11.jpg",
            "backdrop_path": "/6aU1215bF2N6tJ8S8GgQZ8zM0rZ.jpg",
            "runtime": 180,
            "vote_average": 8.0,
            "popularity": 130.6,
            "release_date": "2013-12-25",
            "budget": 100000000,
            "revenue": 392000694,
            "youtube_trailer_id": "iszwuX1AKEK",
            "streaming_platforms": ["Paramount+", "Peacock"],
            "languages": ["English", "French"],
            "awards": ["5 Oscar Nominations", "Golden Globe Winner (Leonardo DiCaprio)"],
            "country": "United States"
        },
        # Romance & Drama
        {
            "title": "La La Land",
            "genres": ["Romance", "Drama", "Comedy"],
            "overview": "Mia, an aspiring actress, serves lattes to movie stars in between auditions and Sebastian, a jazz musician, scrapes by playing cocktail party gigs in dingy bars, but as success mounts they are faced with decisions that begin to fray the fragile fabric of their love affair, and the dreams they worked so hard to maintain in each other threaten to rip them apart.",
            "cast": ["Ryan Gosling", "Emma Stone", "John Legend", "J.K. Simmons"],
            "director": "Damien Chazelle",
            "poster_path": "/uDO8zWDhfVn1muUwsHBZGMj6nGE.jpg",
            "backdrop_path": "/lXhg4n2A5BrU5W25l24X79s5m1L.jpg",
            "runtime": 128,
            "vote_average": 7.9,
            "popularity": 78.4,
            "release_date": "2016-12-09",
            "budget": 30000000,
            "revenue": 447407695,
            "youtube_trailer_id": "0pdqf4P9MB8",
            "streaming_platforms": ["Netflix", "Hulu"],
            "languages": ["English"],
            "awards": ["6 Oscars (Best Director, Actress Emma Stone, Cinematography, Original Score, Original Song, Production Design)"],
            "country": "United States"
        },
        {
            "title": "Whiplash",
            "genres": ["Drama", "Music"],
            "overview": "Under the direction of a ruthless instructor, a talented young drummer begins to pursue perfection at any cost, even his humanity.",
            "cast": ["Miles Teller", "J.K. Simmons", "Paul Reiser", "Melissa Benoist"],
            "director": "Damien Chazelle",
            "poster_path": "/oAxr4xqoP4A2T22F82j9b9P1B7P.jpg",
            "backdrop_path": "/6bb7sVp06fBfP5Tqg8H7fO5s2zP.jpg",
            "runtime": 107,
            "vote_average": 8.4,
            "popularity": 74.5,
            "release_date": "2014-10-10",
            "budget": 3300000,
            "revenue": 48982041,
            "youtube_trailer_id": "7d_jQyGldu4",
            "streaming_platforms": ["Netflix", "Prime Video"],
            "languages": ["English"],
            "awards": ["3 Oscars (Supporting Actor J.K. Simmons, Film Editing, Sound Mixing)"],
            "country": "United States"
        },
        {
            "title": "About Time",
            "genres": ["Romance", "Comedy", "Drama"],
            "overview": "At the age of 21, Tim discovers he can travel in time and change what happens and has happened in his own life. His decision to make his world a better place by getting a girlfriend turns out not to be as easy as you might think.",
            "cast": ["Domhnall Gleeson", "Rachel McAdams", "Bill Nighy", "Tom Hollander"],
            "director": "Richard Curtis",
            "poster_path": "/i65O6J2R64oamn2asW7f4c1j2vV.jpg",
            "backdrop_path": "/eZ216JcE79FwV34BexyvpeP29v6.jpg",
            "runtime": 123,
            "vote_average": 7.9,
            "popularity": 54.2,
            "release_date": "2013-09-04",
            "budget": 12000000,
            "revenue": 87100449,
            "youtube_trailer_id": "T7A810duHvw",
            "streaming_platforms": ["Netflix", "Prime Video"],
            "languages": ["English"],
            "awards": ["Locarno Film Festival Audience Award Winner"],
            "country": "United Kingdom"
        },
        # Asian Cinema / International
        {
            "title": "Parasite",
            "genres": ["Drama", "Thriller", "Comedy"],
            "overview": "All unemployed, Ki-taek's family takes peculiar interest in the wealthy and glamorous Parks for their livelihood until they get entangled in an unexpected incident.",
            "cast": ["Song Kang-ho", "Lee Sun-kyun", "Cho Yeo-jeong", "Choi Woo-shik"],
            "director": "Bong Joon-ho",
            "poster_path": "/7IiTT1wX9Z8mvo3VIvArPANqV6C.jpg",
            "backdrop_path": "/tuFa5f55C42tXgqIIuHjIE5L34T.jpg",
            "runtime": 132,
            "vote_average": 8.5,
            "popularity": 92.5,
            "release_date": "2019-05-30",
            "budget": 11400000,
            "revenue": 263100000,
            "youtube_trailer_id": "5xH0HfJHsaY",
            "streaming_platforms": ["Max", "Hulu"],
            "languages": ["Korean"],
            "awards": ["4 Oscars (Best Picture, Director, Original Screenplay, International Feature Movie)", "Palme d'Or Winner"],
            "country": "South Korea"
        },
        # Anime
        {
            "title": "Spirited Away",
            "genres": ["Anime", "Fantasy", "Adventure"],
            "overview": "A young girl, Chihiro, becomes trapped in a strange new world of spirits. When her parents undergo a mysterious transformation, she must summon the courage to live and work amongst the spirits.",
            "cast": ["Rumi Hiiragi", "Miyu Irino", "Mari Natsuki", "Takashi Naito"],
            "director": "Hayao Miyazaki",
            "poster_path": "/39wmItIWsg5sZMyRUHLkWBcuVCM.jpg",
            "backdrop_path": "/m4TUa2ciEWSlk37rOsjiSIvZDXE.jpg",
            "runtime": 125,
            "vote_average": 8.5,
            "popularity": 87.6,
            "release_date": "2001-07-20",
            "budget": 19000000,
            "revenue": 395880000,
            "youtube_trailer_id": "ByXuk9QqQkk",
            "streaming_platforms": ["Max"],
            "languages": ["Japanese"],
            "awards": ["Oscar Winner (Best Animated Feature)"],
            "country": "Japan"
        },
        {
            "title": "Your Name.",
            "genres": ["Anime", "Romance", "Fantasy", "Drama"],
            "overview": "High schoolers Mitsuha and Taki are complete strangers living separate lives. But one night, they suddenly switch places. Mitsuha wakes up in Taki's body, and he in hers. This bizarre occurrence continues to happen randomly, and the two must adjust their lives around each other.",
            "cast": ["Ryunosuke Kamiki", "Mone Kamishiraishi", "Ryo Narita", "Aoi Yuki"],
            "director": "Makoto Shinkai",
            "poster_path": "/q7G6W3Z23h2tXqYg9m9T2R3rJ1A.jpg",
            "backdrop_path": "/6qP6V2k3F6c8t616sR46sL88c7d.jpg",
            "runtime": 106,
            "vote_average": 8.5,
            "popularity": 74.2,
            "release_date": "2016-08-26",
            "budget": 3400000,
            "revenue": 382238181,
            "youtube_trailer_id": "xU47n012C45",
            "streaming_platforms": ["Crunchyroll", "Prime Video"],
            "languages": ["Japanese"],
            "awards": ["Los Angeles Movie Critics Association Award Winner"],
            "country": "Japan"
        },
        {
            "title": "Princess Mononoke",
            "genres": ["Anime", "Fantasy", "Adventure"],
            "overview": "Ashitaka, a prince of the disappearing Emishi people, is cursed by a demonized boar god and must journey to the west to find a cure. Along the way, he encounters San, a young woman raised by wolves, who leads a fight against human desecration of the forest.",
            "cast": ["Yoji Matsuda", "Yuriko Ishida", "Yuko Tanaka", "Kaoru Kobayashi"],
            "director": "Hayao Miyazaki",
            "poster_path": "/jdb9C4cc6Jj1t50m53e5516Ni2t.jpg",
            "backdrop_path": "/x2qtHX31C5p2l4iTY4v87j9Nzqv.jpg",
            "runtime": 134,
            "vote_average": 8.3,
            "popularity": 62.4,
            "release_date": "1997-07-12",
            "budget": 20000000,
            "revenue": 169785629,
            "youtube_trailer_id": "4OiM_ABiZg4",
            "streaming_platforms": ["Max"],
            "languages": ["Japanese"],
            "awards": ["Japan Academy Prize Winner for Picture of the Year"],
            "country": "Japan"
        },
        # Action & Blockbusters
        {
            "title": "The Matrix",
            "genres": ["Action", "Sci-Fi"],
            "overview": "Set in the 22nd century, The Matrix tells the story of a computer hacker who joins a group of underground insurgents who battle the vast and powerful computers who now rule the earth.",
            "cast": ["Keanu Reeves", "Laurence Fishburne", "Carrie-Anne Moss", "Hugo Weaving"],
            "director": "Lana Wachowski",
            "poster_path": "/hEpWvX6Bp79eLxY1kX5ZZJcme5U.jpg",
            "backdrop_path": "/icmmSD4vTTDKOq2vvdulafOGw93.jpg",
            "runtime": 136,
            "vote_average": 8.2,
            "popularity": 96.4,
            "release_date": "1999-03-30",
            "budget": 63000000,
            "revenue": 463517383,
            "youtube_trailer_id": "vKQi3bBA1y8",
            "streaming_platforms": ["Max", "Netflix"],
            "languages": ["English"],
            "awards": ["4 Oscars (Editing, Sound, Sound Effects, Visual Effects)"],
            "country": "United States"
        },
        {
            "title": "Gladiator",
            "genres": ["Action", "Adventure", "Drama"],
            "overview": "In the year 180, the death of Emperor Marcus Aurelius throws the Roman Empire into chaos. Maximus is one of the Roman army's most capable and trusted generals and a key advisor to the Emperor. As Marcus' devious son Commodus ascends to the throne, Maximus is condemned to death. He escapes, but is captured as a slave and trained as a gladiator.",
            "cast": ["Russell Crowe", "Joaquin Phoenix", "Connie Nielsen", "Oliver Reed"],
            "director": "Ridley Scott",
            "poster_path": "/ty87ILCo5OB7444HN6g53036PcB.jpg",
            "backdrop_path": "/e52v517mHj856tY5n643Z2H6HNt.jpg",
            "runtime": 155,
            "vote_average": 8.2,
            "popularity": 99.1,
            "release_date": "2000-05-05",
            "budget": 103000000,
            "revenue": 460583960,
            "youtube_trailer_id": "owK1qxDselE",
            "streaming_platforms": ["Prime Video", "Paramount+"],
            "languages": ["English"],
            "awards": ["5 Oscars (Best Picture, Actor Russell Crowe, Costume Design, Sound, Visual Effects)"],
            "country": "United States"
        },
        {
            "title": "Blade Runner 2049",
            "genres": ["Sci-Fi", "Thriller", "Mystery"],
            "overview": "Thirty years after the events of the first film, a new blade runner, LAPD Officer K, unearths a long-buried secret that has the potential to plunge what's left of society into chaos. K's discovery leads him on a quest to find Rick Deckard, a former LAPD blade runner who has been missing for 30 years.",
            "cast": ["Ryan Gosling", "Harrison Ford", "Ana de Armas", "Sylvester Stallner", "Jared Leto"],
            "director": "Denis Villeneuve",
            "poster_path": "/gajPR2JvM6bC8k6d8q43j79C0eW.jpg",
            "backdrop_path": "/mVr4UjXur35fU22v71W02x58p45.jpg",
            "runtime": 164,
            "vote_average": 7.5,
            "popularity": 82.3,
            "release_date": "2017-10-06",
            "budget": 150000000,
            "revenue": 259239655,
            "youtube_trailer_id": "gCcx85zVzEc",
            "streaming_platforms": ["Hulu", "Max"],
            "languages": ["English"],
            "awards": ["2 Oscars (Best Cinematography, Visual Effects)"],
            "country": "United States"
        },
        {
            "title": "Knives Out",
            "genres": ["Comedy", "Mystery", "Crime"],
            "overview": "When renowned crime novelist Harlan Thrombey is found dead at his estate just after his 85th birthday, the inquisitive and debonair Detective Benoit Blanc is mysteriously enlisted to investigate. From Harlan's dysfunctional family to his devoted staff, Blanc sifts through a web of red herrings and self-serving lies to uncover the truth.",
            "cast": ["Daniel Craig", "Chris Evans", "Ana de Armas", "Jamie Lee Curtis"],
            "director": "Rian Johnson",
            "poster_path": "/3BtCoG1ZCnCrp4tSXe3223fDygP.jpg",
            "backdrop_path": "/7M5XG1LSDG5t6o2v2m17c76yM1Z.jpg",
            "runtime": 130,
            "vote_average": 7.9,
            "popularity": 74.8,
            "release_date": "2019-11-27",
            "budget": 40000000,
            "revenue": 312897920,
            "youtube_trailer_id": "qGqiHJTsRkQ",
            "streaming_platforms": ["Prime Video"],
            "languages": ["English", "Spanish"],
            "awards": ["Oscar Nominated (Best Original Screenplay)"],
            "country": "United States"
        },
        {
            "title": "Avengers: Endgame",
            "genres": ["Action", "Sci-Fi", "Adventure"],
            "overview": "After the devastating events of Avengers: Infinity War, the universe is in ruins. With the help of remaining allies, the Avengers assemble once more in order to reverse Thanos' actions and restore balance to the universe.",
            "cast": ["Robert Downey Jr.", "Chris Evans", "Mark Ruffalo", "Chris Hemsworth", "Scarlett Johansson"],
            "director": "Anthony Russo",
            "poster_path": "/or06g58d0Jf3kcyh45IWF2iR36q.jpg",
            "backdrop_path": "/7RyGs46A1r2LzTwgUu1pS9kE0C3.jpg",
            "runtime": 181,
            "vote_average": 8.2,
            "popularity": 240.2,
            "release_date": "2019-04-26",
            "budget": 356000000,
            "revenue": 2797800564,
            "youtube_trailer_id": "TcMBFSGVi1A",
            "streaming_platforms": ["Disney+"],
            "languages": ["English", "Japanese"],
            "awards": ["Oscar Nominated (Best Visual Effects)"],
            "country": "United States"
        },
        {
            "title": "The Grand Budapest Hotel",
            "genres": ["Comedy", "Drama"],
            "overview": "The writer tells the story of his stay at the Grand Budapest Hotel in the 1930s, where he befriended the legendary concierge Gustave H. and his young protege Zero Moustafa.",
            "cast": ["Ralph Fiennes", "Tony Revolori", "Saoirse Ronan", "Adrien Brody"],
            "director": "Wes Anderson",
            "poster_path": "/e6i2LI9vVfI626Lz95P74k8H82f.jpg",
            "backdrop_path": "/uS5DkHshL2qT32K3Bndh61pG5jC.jpg",
            "runtime": 100,
            "vote_average": 8.0,
            "popularity": 45.3,
            "release_date": "2014-03-07",
            "budget": 25000000,
            "revenue": 172900000,
            "youtube_trailer_id": "1Fg5iWmQjwk",
            "streaming_platforms": ["Max", "Hulu"],
            "languages": ["English", "French"],
            "awards": ["4 Oscars (Costume Design, Makeup, Original Score, Production Design)"],
            "country": "Germany"
        },
        {
            "title": "Spider-Man: Into the Spider-Verse",
            "genres": ["Anime", "Action", "Adventure", "Sci-Fi"],
            "overview": "Miles Morales is juggling his life between being a high school student and being a spider-man. When Wilson \"Kingpin\" Fisk uses a super collider, others from across the Spider-Verse are pulled into this dimension.",
            "cast": ["Shameik Moore", "Jake Johnson", "Hailee Steinfeld", "Mahershala Ali"],
            "director": "Bob Persichetti",
            "poster_path": "/iiBEZKi6m776iIH2Dev4d3bOVHB.jpg",
            "backdrop_path": "/7ad654249a2U7wceas6GZ4Kd79a.jpg",
            "runtime": 117,
            "vote_average": 8.4,
            "popularity": 135.2,
            "release_date": "2018-12-14",
            "budget": 90000000,
            "revenue": 375540831,
            "youtube_trailer_id": "g4Hbz2yLXGE",
            "streaming_platforms": ["Disney+", "Hulu"],
            "languages": ["English", "Spanish"],
            "awards": ["Oscar Winner (Best Animated Feature)"],
            "country": "United States"
        },
        {
            "title": "Your Lie in April",
            "genres": ["Anime", "Drama", "Romance", "Music"],
            "overview": "Kousei Arima is a piano prodigy who loses his ability to play after his mother's death. His life changes when he meets Kaori Miyazono, a free-spirited violinist who helps him return to the music world.",
            "cast": ["Natsuki Hanae", "Risa Taneda", "Ayane Sakura", "Yuki Kaji"],
            "director": "Kyohei Ishiguro",
            "poster_path": "/4oWic8b6D2t0s3gZfJ3e76a6eW1.jpg",
            "backdrop_path": "/1kP4u3t1c5g9v6t8e7x7w7s7t7e.jpg",
            "runtime": 110,
            "vote_average": 8.6,
            "popularity": 32.4,
            "release_date": "2014-10-09",
            "budget": 2000000,
            "revenue": 10000000,
            "youtube_trailer_id": "3Z1H2U3g_gI",
            "streaming_platforms": ["Crunchyroll", "Hulu"],
            "languages": ["Japanese"],
            "awards": ["Sugoi Japan Award Winner"],
            "country": "Japan"
        }
    ]

    # Additional movies dynamically generated to total ~200
    random.seed(42)
    genres_pool = ["Action", "Comedy", "Romance", "Crime", "Thriller", "Fantasy", "Sci-Fi", "Anime", "Drama", "Adventure", "Mystery"]
    directors_pool = ["Christopher Nolan", "Quentin Tarantino", "David Fincher", "Martin Scorsese", "Damien Chazelle", "Bong Joon-ho", "Hayao Miyazaki", "Denis Villeneuve", "Ridley Scott", "Steven Spielberg", "James Cameron", "Greta Gerwig"]
    actors_pool = ["Leonardo DiCaprio", "Brad Pitt", "Ryan Gosling", "Emma Stone", "Matthew McConaughey", "Anne Hathaway", "Jessica Chastain", "Christian Bale", "Scarlett Johansson", "Matt Damon", "J.K. Simmons", "Ana de Armas", "Song Kang-ho", "Timothee Chalamet", "Florence Pugh", "Zendaya"]
    platforms_pool = ["Netflix", "Prime Video", "Disney+", "Max", "Hulu", "Apple TV+"]
    languages_pool = ["English", "Japanese", "Spanish", "French", "Korean", "German"]
    countries_pool = ["United States", "Japan", "South Korea", "United Kingdom", "France", "Germany", "Canada"]

    # Sample posters and backdrops pool to cycle through for procedural movies
    posters_pool = [
        "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg", "/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg", "/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        "/5aGHa5X2mSOXXt2nQ6i42886n0V.jpg", "/ty87ILCo5OB7444HN6g53036PcB.jpg", "/d5i25CcVzb7tU2kyUp6cu7bhU47.jpg",
        "/pB8BM7pdSp6B66W0Z7097GbbFM5.jpg", "/3BtCoG1ZCnCrp4tSXe3223fDygP.jpg", "/rygzy2Tgl4ArKi2Igi370V8XLG0.jpg",
        "/oAxr4xqoP4A2T22F82j9b9P1B7P.jpg", "/7IiTT1wX9Z8mvo3VIvArPANqV6C.jpg", "/uDO8zWDhfVn1muUwsHBZGMj6nGE.jpg",
        "/iiBEZKi6m776iIH2Dev4d3bOVHB.jpg", "/4oWic8b6D2t0s3gZfJ3e76a6eW1.jpg", "/y2Y474o5n24XGUE58Z5v7nnTy96.jpg",
        "/gajPR2JvM6bC8k6d8q43j79C0eW.jpg", "/f89U3wzqrjVnH5bZLMccOnIKo3d.jpg", "/jwwxzIY90S6Uo2S70d7Sj0a5r11.jpg",
        "/or06g58d0Jf3kcyh45IWF2iR36q.jpg", "/3bhkrj6PjOqzbHph0Z4r7UNj2wW.jpg", "/aKuFi14FG7jz8547vLz74wY6XzH.jpg",
        "/e6i2LI9vVfI626Lz95P74k8H82f.jpg", "/kve201gZzXmZpxCVRzVP1qg17Cc.jpg", "/yk4J4ui3CEk6FRHGnnZodwfOI4w.jpg"
    ]
    backdrops_pool = [
        "/xJHokZbljvjCNmzb04z2tHNi65e.jpg", "/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg", "/nMKdUUepR0i5zn0y1T4CsSB5chy.jpg",
        "/j976sb7tPXuB6v2UjqpvUiLvgoY.jpg", "/lh4aVh0vNhgzcuV67v2GW5a4J4v.jpg", "/9n52P0767uV34569uVjA6tA9fgP.jpg",
        "/s30386UUe5ZCRnu57vSIUz20ecV.jpg", "/2oZhyved3jZQq7wjoi7QjOdhb6x.jpg", "/lh4aVh0vNhgzcuV67v2GW5a4J4v.jpg",
        "/6qP6V2k3F6c8t616sR46sL88c7d.jpg", "/zN4f61RLCcKr7t31XJqkvISEui7.jpg", "/tuFa5f55C42tXgqIIuHjIE5L34T.jpg",
        "/7M5XG1LSDG5t6o2v2m17c76yM1Z.jpg", "/1kP4u3t1c5g9v6t8e7x7w7s7t7e.jpg", "/lh4aVh0vNhgzcuV67v2GW5a4J4v.jpg",
        "/iiBEZKi6m776iIH2Dev4d3bOVHB.jpg", "/lh4aVh0vNhgzcuV67v2GW5a4J4v.jpg", "/lh4aVh0vNhgzcuV67v2GW5a4J4v.jpg",
        "/lh4aVh0vNhgzcuV67v2GW5a4J4v.jpg", "/lh4aVh0vNhgzcuV67v2GW5a4J4v.jpg", "/lh4aVh0vNhgzcuV67v2GW5a4J4v.jpg",
        "/lh4aVh0vNhgzcuV67v2GW5a4J4v.jpg", "/lh4aVh0vNhgzcuV67v2GW5a4J4v.jpg", "/lh4aVh0vNhgzcuV67v2GW5a4J4v.jpg"
    ]

    titles_pool = [
        ("The Quantum Paradox", "Sci-Fi"), ("Cyber City 2099", "Sci-Fi"), ("Stellar Oasis", "Sci-Fi"),
        ("Beyond the Horizon", "Adventure"), ("Shadows of Cairo", "Adventure"), ("Ocean's Depths", "Adventure"),
        ("Neon Shadows", "Crime"), ("The Syndicate", "Crime"), ("Double Cross in Brooklyn", "Crime"),
        ("Deadly Whisper", "Thriller"), ("The Informant", "Thriller"), ("Room 101", "Thriller"),
        ("Laughter in Paris", "Comedy"), ("Family Feud", "Comedy"), ("Accidental Detectives", "Comedy"),
        ("Summer of '98", "Romance"), ("Midnight Coffee", "Romance"), ("Strangers in Tokyo", "Romance"),
        ("Whisper of the Wind", "Anime"), ("Spirit Journey", "Anime"), ("Mecha Vanguard", "Anime"),
        ("Chrono Triggered", "Fantasy"), ("Realm of Dragons", "Fantasy"), ("The Lost Elixir", "Fantasy"),
        ("A Life Rewritten", "Drama"), ("The Last Stand", "Drama"), ("Broken Mirrors", "Drama")
    ]

    # Fetch real movies from TMDb API
    import os
    from .tmdb import sync_movies_from_tmdb, search_tmdb_movies, fetch_tmdb_movie_by_id
    
    api_key = os.getenv("TMDB_API_KEY", "")
    if not api_key:
        print("WARNING: TMDB_API_KEY is not set. Skipping TMDb sync and curated title "
              "ingestion - only the tiny hand-crafted fallback list below will be seeded.")
    synced = 0
    if api_key:
        try:
            print("Fetching real popular movies from TMDb API...")
            synced = sync_movies_from_tmdb(db, api_key, count=150)
        except Exception as e:
            print(f"Failed to fetch from TMDb: {e}")

    # Ensure a strong, well-regarded slate of Horror titles is always present.
    # Metadata (poster, backdrop, cast, etc.) is pulled live from TMDb by title
    # search rather than hand-typed, so posters are guaranteed accurate instead
    # of risking broken/guessed image paths.
    print("Ensuring curated Horror titles are present...")
    CURATED_HORROR_TITLES = [
        "The Shining", "Hereditary", "Get Out", "The Exorcist", "A Quiet Place",
        "Psycho", "The Conjuring", "Midsommar", "It Follows", "The Babadook",
        "Us", "Rosemary's Baby", "The Texas Chain Saw Massacre", "Alien",
        "The Witch", "Halloween", "Sinister", "Insidious", "It",
        "28 Days Later", "The Thing", "Nosferatu", "Barbarian", "Talk to Me"
    ]
    horror_added = 0
    try:
        for title in CURATED_HORROR_TITLES:
            existing = db.query(Movie).filter(Movie.title == title).first()
            if existing:
                continue
            matches = search_tmdb_movies(api_key, title)
            if matches:
                result = fetch_tmdb_movie_by_id(db, matches[0]["tmdb_id"], api_key)
                if result:
                    horror_added += 1
    except Exception as e:
        print(f"Failed to ensure curated horror titles: {e}")
    print(f"Curated Horror titles added: {horror_added}")

    # NOTE: Poster backfill is intentionally NOT run here. seed_database() runs
    # synchronously inside FastAPI's startup event - a long sequential loop of
    # live TMDb network calls here would block the entire app from finishing
    # startup (every request hangs until it's done). Backfill now runs as a
    # non-blocking background task after startup instead - see main.py.

    # Ensure classic hand-crafted real movies are always present in the database
    print("Adding hand-crafted classics if missing...")
    for m in real_movies:
        existing = db.query(Movie).filter(Movie.title == m["title"]).first()
        if not existing:
            movie = Movie(**m)
            db.add(movie)
    db.commit()

    print(f"Total Movies Seeded: {db.query(Movie).count()}")

    print("Seeding users...")
    # Seed 80 synthetic users
    # Pre-hash password for swift seeding
    hashed_pwd = get_password_hash("password123")
    admin_hashed_pwd = get_password_hash("Priyanshi0310")
    
    users = []
    
    # Hand-craft a couple of test users
    admin_user = db.query(User).filter(User.email == "priv0907@gmail.com").first()
    if not admin_user:
        admin_user = User(
            name="Admin User",
            email="priv0907@gmail.com",
            password_hash=admin_hashed_pwd,
            preferred_genres=["Sci-Fi", "Action", "Thriller"],
            preferred_languages=["English", "Japanese"],
            preferred_actors=["Leonardo DiCaprio", "Matthew McConaughey"],
            preferred_directors=["Christopher Nolan", "Denis Villeneuve"],
            preferred_runtime="90-120 mins",
            preferred_mood="Mind-bending",
            age=28,
            region="North America"
        )
        db.add(admin_user)
    else:
        admin_user.password_hash = admin_hashed_pwd
    users.append(admin_user)

    guest_user = db.query(User).filter(User.email == "guest@netflix.com").first()
    if not guest_user:
        guest_user = User(
            name="Guest User",
            email="guest@netflix.com",
            password_hash=hashed_pwd,
            preferred_genres=["Comedy", "Romance"],
            preferred_languages=["English"],
            preferred_actors=["Emma Stone", "Ryan Gosling"],
            preferred_directors=["Damien Chazelle"],
            preferred_runtime="Under 90 mins",
            preferred_mood="Happy",
            age=22,
            region="Europe"
        )
        db.add(guest_user)
    else:
        guest_user.password_hash = hashed_pwd
        guest_user.preferred_genres = ["Comedy", "Romance"]
        guest_user.preferred_mood = "Happy"
    users.append(guest_user)

    # Let's generate synthetic user clusters to make collaborative filtering patterns clean
    # Cluster 1: Sci-Fi & Action Lovers (Nolan/Villeneuve fans)
    # Cluster 2: Romance & Drama & Anime Lovers (Miyazaki/Shinkai fans)
    # Cluster 3: Crime & Thriller & Tarantino fans
    # Cluster 4: Comedy & Music fans
    
    for i in range(1, 80):
        cluster = i % 4
        if cluster == 0:
            genres = ["Sci-Fi", "Action", "Adventure"]
            directors = ["Christopher Nolan", "Denis Villeneuve", "Ridley Scott"]
            actors = ["Leonardo DiCaprio", "Matthew McConaughey", "Christian Bale"]
            mood = "Mind-bending"
        elif cluster == 1:
            genres = ["Anime", "Fantasy", "Romance", "Drama"]
            directors = ["Hayao Miyazaki", "Makoto Shinkai", "Damien Chazelle"]
            actors = ["Emma Stone", "Ryan Gosling"]
            mood = "Happy"
        elif cluster == 2:
            genres = ["Crime", "Thriller", "Drama"]
            directors = ["Quentin Tarantino", "David Fincher", "Martin Scorsese"]
            actors = ["Brad Pitt", "Leonardo DiCaprio", "Samuel L. Jackson"]
            mood = "Dark"
        else:
            genres = ["Comedy", "Romance", "Music"]
            directors = ["Damien Chazelle", "Wes Anderson"]
            actors = ["Emma Stone", "Ryan Gosling", "Jonah Hill", "Margot Robbie"]
            mood = "Feel-good"

        email = f"user{i}@netflix.com"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                name=f"User {i}",
                email=email,
                password_hash=hashed_pwd,
                preferred_genres=genres,
                preferred_languages=["English", "Japanese"] if "Anime" in genres else ["English"],
                preferred_actors=actors,
                preferred_directors=directors,
                preferred_runtime=random.choice(["Under 90 mins", "90-120 mins", "Over 2 hours"]),
                preferred_mood=mood,
                age=random.randint(18, 55),
                region=random.choice(countries_pool)
            )
            db.add(user)
        users.append(user)

    db.commit()
    print("Users seeded.")

    print("Seeding ratings...")
    # Seed collaborative ratings
    # We want consistent ratings matching user clusters to make predictions solid
    ratings_count = 0
    all_movies = db.query(Movie).all()
    all_users = db.query(User).all()
    
    for u in all_users:
        # Determine user interest profile
        u_genres = set(u.preferred_genres)
        u_directors = set(u.preferred_directors)
        u_actors = set(u.preferred_actors)
        
        # Decide which movies this user has watched and rated
        # Let's rate ~20-35 movies per user
        movies_to_rate = random.sample(all_movies, k=random.randint(20, 35))
        
        for m in movies_to_rate:
            # Base rating is random from 2.5 to 4.5
            rating_val = round(random.uniform(2.5, 4.0), 1)
            
            # Match factors: boost rating if genre, director, or actor matches preferences
            genre_overlap = len(u_genres.intersection(m.genres))
            if genre_overlap > 0:
                rating_val += 0.4 * genre_overlap
            
            if m.director in u_directors:
                rating_val += 0.6
                
            actor_overlap = len(u_actors.intersection(m.cast))
            if actor_overlap > 0:
                rating_val += 0.3 * actor_overlap
                
            # Clamp rating between 1.0 and 5.0
            rating_val = max(1.0, min(5.0, round(rating_val, 1)))
            
            rating = Rating(
                user_id=u.id,
                movie_id=m.id,
                rating=rating_val
            )
            db.add(rating)
            ratings_count += 1

            # Seed watch history and watchlists for some rated movies
            action_type = "liked" if rating_val >= 4.0 else ("watched" if rating_val >= 3.0 else "viewed")
            h = History(
                user_id=u.id,
                movie_id=m.id,
                action=action_type
            )
            db.add(h)

            if rating_val >= 4.5 and random.random() < 0.3:
                w = Watchlist(
                    user_id=u.id,
                    movie_id=m.id,
                    status="Completed"
                )
                db.add(w)
            elif rating_val <= 3.0 and random.random() < 0.15:
                w = Watchlist(
                    user_id=u.id,
                    movie_id=m.id,
                    status="Dropped"
                )
                db.add(w)

        # Also add some active watchlists that are "Want to Watch"
        want_to_watch_movies = random.sample(all_movies, k=random.randint(3, 8))
        for m in want_to_watch_movies:
            # Check if rating already exists, if so skip
            has_rating = m.id in {r.id for r in movies_to_rate}
            
            w_exists = db.query(Watchlist).filter_by(user_id=u.id, movie_id=m.id).first()
            if not w_exists:
                w = Watchlist(
                    user_id=u.id,
                    movie_id=m.id,
                    status=random.choice(["Want to Watch", "Watching"])
                )
                db.add(w)

    db.commit()
    print(f"Ratings seeded: {ratings_count}")
    print("Database seeding completed successfully!")
    db.close()

if __name__ == "__main__":
    seed_database()