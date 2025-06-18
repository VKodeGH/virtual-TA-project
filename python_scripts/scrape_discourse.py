import json
import time
import os
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

# Configuration
DISCOURSE_URL = "https://discourse.onlinedegree.iitm.ac.in"
CATEGORY_PATH = "courses/tds-kb/34"
START_DATE = datetime(2025, 1, 1, tzinfo=timezone.utc)
END_DATE = datetime(2025, 4, 14, tzinfo=timezone.utc)

# Get credentials
DISCOURSE_T = os.getenv('DISCOURSE_T')
DISCOURSE_FORUM_SESSION = os.getenv('DISCOURSE_FORUM_SESSION')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not all([DISCOURSE_T, DISCOURSE_FORUM_SESSION]):
    raise ValueError("Missing Discourse cookies in .env file")
if not GEMINI_API_KEY:
    raise ValueError("Missing Gemini API key in .env file")

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Path setup
ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / 'data' / 'discourse-posts'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = ROOT_DIR / 'data' / 'image_descriptions_cache.json'

# Load or initialize image description cache
if CACHE_FILE.exists():
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        image_cache = json.load(f)
else:
    image_cache = {}

def create_session():
    """Create authenticated session with cookies"""
    session = requests.Session()
    session.cookies.update({
        '_t': DISCOURSE_T,
        '_forum_session': DISCOURSE_FORUM_SESSION
    })
    return session

def get_image_description(image_url, alt_text=""):
    """Get image description from Gemini with caching and rate limit handling"""
    cache_key = f"{image_url}|{alt_text}"
    if cache_key in image_cache:
        return image_cache[cache_key]
    try:
        response = model.generate_content(
            f"Describe this educational image in detail for student assistance. Alt text: '{alt_text}'. Image URL: {image_url}"
        )
        description = response.text.strip()
        image_cache[cache_key] = description
        # Save cache after every new entry
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(image_cache, f, indent=2, ensure_ascii=False)
        time.sleep(2)  # Add delay to avoid hitting rate limits
        return description
    except Exception as e:
        error_msg = f"Image description unavailable: {str(e)}"
        image_cache[cache_key] = error_msg
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(image_cache, f, indent=2, ensure_ascii=False)
        return error_msg

def process_post(post):
    """Process post content and replace images with Gemini descriptions"""
    soup = BeautifulSoup(post['cooked'], 'html.parser')
    for img in soup.find_all('img'):
        img_url = img['src']
        alt_text = img.get('alt', '')
        if img_url.startswith('/'):
            img_url = f"{DISCOURSE_URL}{img_url}"
        description = get_image_description(img_url, alt_text)
        img.replace_with(f"[Image Description: {description}]")
    return {
        "id": post['id'],
        "topic_id": post['topic_id'],
        "username": post['username'],
        "created_at": post['created_at'],
        "url": f"{DISCOURSE_URL}/t/{post['topic_id']}/{post['post_number']}",
        "content": str(soup)
    }

def safe_request(session, url, max_retries=5, initial_delay=1):
    """Handle requests with exponential backoff"""
    retries = 0
    while retries < max_retries:
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            wait_time = initial_delay * (2 ** retries)
            print(f"⚠️ Error: {str(e)}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            retries += 1
    raise Exception(f"❌ Failed after {max_retries} retries for URL: {url}")

def scrape_discourse():
    """Main scraping function with error handling and progress saving"""
    session = create_session()
    all_posts = []
    page = 0

    try:
        while True:
            topics_url = f"{DISCOURSE_URL}/c/{CATEGORY_PATH}.json?page={page}"
            print(f"\n🔍 Page {page + 1}: {topics_url}")
            
            response = safe_request(session, topics_url)
            data = response.json()

            topic_list = data.get('topic_list', {})
            if not isinstance(topic_list, dict):
                raise ValueError("Unexpected API response format")
            
            topics = topic_list.get('topics', [])
            print(f"📚 Found {len(topics)} topics")
            
            if not topics:
                break

            # Process topics
            for topic in topics:
                topic_id = topic['id']
                created_at = datetime.fromisoformat(
                    topic['created_at'].replace('Z', '+00:00')
                ).astimezone(timezone.utc)
                
                if not (START_DATE <= created_at <= END_DATE):
                    continue

                # Get topic posts
                posts_url = f"{DISCOURSE_URL}/t/{topic_id}.json"
                print(f"  🔍 Processing topic {topic_id}")
                
                posts_response = safe_request(session, posts_url)
                posts_data = posts_response.json()
                
                # Process all posts in topic
                for post in posts_data.get('post_stream', {}).get('posts', []):
                    processed_post = process_post(post)
                    all_posts.append(processed_post)
                
                time.sleep(0.5)  # Rate limit between topics

            # Save progress after each page
            with open(OUTPUT_DIR / 'discourse_posts_temp.json', 'w', encoding='utf-8') as f:
                json.dump(all_posts, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved {len(all_posts)} posts (temp file)")

            # Check for more pages
            if not topic_list.get('more_topics_url'):
                break
                
            page += 1
            time.sleep(1)  # Rate limit between pages

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    finally:
        # Save results to correct location
        output_file = OUTPUT_DIR / 'discourse_posts.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_posts, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved {len(all_posts)} posts to {output_file}")

if __name__ == "__main__":
    scrape_discourse()
