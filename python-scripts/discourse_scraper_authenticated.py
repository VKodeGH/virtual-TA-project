import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from tqdm import tqdm
import json

# Your session cookie (_t value only, not the full cookie header)
DISCOURSE_COOKIE = "u8yV1RNWvvd6Cs7MHt8bbfsh8y3bpseO6RrheFxDBf1OCnSwAkjpUARf49CGn1G003s4ER2GGQvKRhTvErMynVrYdBpUCFmskR8EM5u%2FmZYVdroyZx25AkyE%2F6LNWJLnQePB%2FQ4%2F5BM3f7VaF5hMeyflf%2BPp%2BULQQ%2BeONqf%2Bf8Ftv1H12UDItw3iHPsZvUMiZwgLS60n1SiIjUUBIdvxHonqwE1rs05AD%2BFsnw%2B4p4WREtuhZsqWLOjENIo7cluifRNP2gKNxO6hyWvEi%2BEuh0fVdVx1%2Fzt%2B1kNlstlZUCoudAEg0aDUMWQYlMsOSmwasdRpAg%3D%3D--frjrYdOj71BLS7As--MzGIsvlXiTLeV%2Bp3uYFVuw%3D%3D"

session = requests.Session()
session.cookies.set("_t", DISCOURSE_COOKIE, domain="discourse.onlinedegree.iitm.ac.in")
session.headers.update({"User-Agent": "Mozilla/5.0"})

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"

def get_topic_ids(category_slug="courses/tds-kb", category_id=34):
    topics = []
    for page in tqdm(range(0, 20)):  # Adjust if you want more pages
        url = f"{BASE_URL}/c/{category_slug}/{category_id}.json?page={page}"
        r = session.get(url)
        if r.status_code != 200:
            break
        data = r.json()
        new_topics = data["topic_list"]["topics"]
        if not new_topics:
            break
        topics.extend(new_topics)
    return topics

def get_posts_in_topic(topic_id):
    r = session.get(f"{BASE_URL}/t/{topic_id}.json")
    if r.status_code != 200:
        return []
    data = r.json()
    return [
        {
            "username": post["username"],
            "created_at": post["created_at"],
            "content": BeautifulSoup(post["cooked"], "html.parser").get_text(),
            "post_url": f"{BASE_URL}/t/{topic_id}/{post['post_number']}"
        }
        for post in data["post_stream"]["posts"]
    ]

all_posts = []
topics = get_topic_ids()

for topic in tqdm(topics):
    # Parse created_at as timezone-aware datetime (UTC)
    created_at = datetime.fromisoformat(topic["created_at"].replace("Z", "+00:00"))
    # Compare with a timezone-aware datetime for Jan 1, 2025 UTC
    if (created_at >= datetime(2025, 1, 1, tzinfo=timezone.utc)) and \
   (created_at <= datetime(2025, 4, 14, tzinfo=timezone.utc)):
        posts = get_posts_in_topic(topic["id"])
        all_posts.extend(posts)

# Save the scraped posts into a JSON file
# Save to your existing data/discourse-posts folder
with open("../data/discourse-posts/discourse_posts.json", "w", encoding="utf-8") as f:
    json.dump(all_posts, f, indent=2, ensure_ascii=False)

print(f"Scraped {len(all_posts)} posts.")
