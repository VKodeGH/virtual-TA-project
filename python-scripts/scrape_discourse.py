import requests
import json
import os
import time
from datetime import datetime, date
from bs4 import BeautifulSoup
import re

class TDSDiscourseScraper:
    def __init__(self):
        self.base_url = "https://discourse.onlinedegree.iitm.ac.in"
        self.data_dir = "../data/discourse-posts"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_topics_list(self, category_slug="", page=0):
        """Get list of topics from discourse"""
        if category_slug:
            url = f"{self.base_url}/c/{category_slug}.json?page={page}"
        else:
            url = f"{self.base_url}/latest.json?page={page}"
            
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching topics: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_topic_details(self, topic_id):
        """Get detailed posts from a topic"""
        url = f"{self.base_url}/t/{topic_id}.json"
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching topic {topic_id}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching topic {topic_id}: {e}")
            return None
    
    def is_date_in_range(self, date_str):
        """Check if date is between Jan 1, 2025 and Apr 14, 2025"""
        try:
            post_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
            start_date = date(2025, 1, 1)
            end_date = date(2025, 4, 14)
            return start_date <= post_date <= end_date
        except:
            return False
    
    def clean_html_content(self, html_content):
        """Clean HTML and extract text"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text().strip()
    
    def process_topic(self, topic_data):
        """Process a single topic and its posts"""
        posts = []
        topic_info = topic_data.get('post_stream', {})
        
        for post in topic_info.get('posts', []):
            # Check if post is in our date range
            if not self.is_date_in_range(post.get('created_at', '')):
                continue
                
            processed_post = {
                'source': 'discourse',
                'topic_id': topic_data.get('id'),
                'topic_title': topic_data.get('title', ''),
                'topic_url': f"{self.base_url}/t/{topic_data.get('slug', '')}/{topic_data.get('id')}",
                'post_id': post.get('id'),
                'post_number': post.get('post_number'),
                'username': post.get('username', ''),
                'created_at': post.get('created_at'),
                'raw_content': post.get('raw', ''),
                'cooked_content': self.clean_html_content(post.get('cooked', '')),
                'reply_count': post.get('reply_count', 0),
                'type': 'discourse_post'
            }
            posts.append(processed_post)
        
        return posts
    
    def scrape_discourse_posts(self, max_pages=10):
        """Main scraping function"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        all_posts = []
        
        print("Starting Discourse scraping...")
        
        for page in range(max_pages):
            print(f"Scraping page {page + 1}/{max_pages}")
            
            # Get topics list
            topics_data = self.get_topics_list(page=page)
            if not topics_data:
                break
                
            topics = topics_data.get('topic_list', {}).get('topics', [])
            if not topics:
                break
            
            for i, topic in enumerate(topics):
                topic_id = topic.get('id')
                created_at = topic.get('created_at', '')
                
                # Skip if topic is outside our date range
                if not self.is_date_in_range(created_at):
                    continue
                
                print(f"  Processing topic {i+1}/{len(topics)}: {topic.get('title', '')[:50]}...")
                
                # Get detailed topic data
                topic_details = self.get_topic_details(topic_id)
                if topic_details:
                    posts = self.process_topic(topic_details)
                    all_posts.extend(posts)
                
                # Be respectful to the server
                time.sleep(0.5)
        
        # Save all posts
        output_file = os.path.join(self.data_dir, 'discourse_posts.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_posts, f, indent=2, ensure_ascii=False)
        
        print(f"Scraped {len(all_posts)} discourse posts")
        print(f"Data saved to: {output_file}")
        return all_posts

if __name__ == "__main__":
    scraper = TDSDiscourseScraper()
    posts = scraper.scrape_discourse_posts(max_pages=5)  # Start with 5 pages
    print("Discourse scraping completed!")
