import urllib.request
import urllib.parse
import json

api_key = "2d11825663306373fbd924fcfb975415"
headers = {'User-Agent': 'Mozilla/5.0'}

romcom_titles = [
    "How to Lose a Guy in 10 Days",
    "10 Things I Hate About You",
    "Love Actually",
    "The Proposal",
    "50 First Dates",
    "13 Going on 30",
    "The Holiday",
    "Sweet Home Alabama",
    "Notting Hill",
    "Crazy, Stupid, Love.",
    "The Notebook",
    "A Walk to Remember",
    "Pride & Prejudice",
    "My Big Fat Greek Wedding",
    "She's the Man",
    "Serendipity",
    "27 Dresses",
    "Definitely, Maybe",
    "You've Got Mail",
    "Sleepless in Seattle",
    "Silver Linings Playbook",
    "Friends with Benefits",
    "No Strings Attached",
    "He's Just Not That Into You",
    "The Devil Wears Prada",
    "Confessions of a Shopaholic",
    "Maid in Manhattan",
    "Along Came Polly",
    "Just Friends",
    "Forgetting Sarah Marshall"
]

results_map = {}

print("Searching TMDb for romance classics...")
for title in romcom_titles:
    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={urllib.parse.quote(title)}&language=en-US&page=1"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as res:
            data = json.loads(res.read().decode('utf-8'))
            results = data.get('results', [])
            if results:
                match = results[0]
                results_map[title] = {
                    "id": match['id'],
                    "title": match['title'],
                    "release_date": match.get('release_date')
                }
                print(f"Match: {title} -> {match['title']} ({match['id']}, {match.get('release_date')})")
            else:
                print(f"No match for {title}")
    except Exception as e:
        print(f"Error searching {title}: {e}")

print("\nJSON representation:")
print(json.dumps(results_map, indent=2))
