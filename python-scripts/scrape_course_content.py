import requests
import os
import json
from bs4 import BeautifulSoup
import re
from datetime import datetime

class TDSCourseScraper:
    def __init__(self):
        # TDS course content repository
        self.base_url = "https://api.github.com/repos/sanand0/tools-in-data-science-public"
        self.raw_base_url = "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/main"
        self.data_dir = "../data/course-content"
        
    def get_all_markdown_files(self):
        """Get all .md files from the repository"""
        print("Fetching course content files...")
        
        # Get repository tree
        tree_url = f"{self.base_url}/git/trees/main?recursive=1"
        response = requests.get(tree_url)
        
        if response.status_code != 200:
            print(f"Error fetching repository tree: {response.status_code}")
            return []
        
        tree_data = response.json()
        md_files = []
        
        # Filter for .md files
        for item in tree_data.get('tree', []):
            if item['path'].endswith('.md') and item['type'] == 'blob':
                md_files.append(item['path'])
        
        print(f"Found {len(md_files)} markdown files")
        return md_files
    
    def download_file_content(self, file_path):
        """Download content of a specific file"""
        url = f"{self.raw_base_url}/{file_path}"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.text
        else:
            print(f"Error downloading {file_path}: {response.status_code}")
            return None
    
    def process_markdown_content(self, content, file_path):
        """Process and structure markdown content"""
        return {
            'source': 'course_content',
            'file_path': file_path,
            'content': content,
            'scraped_at': datetime.now().isoformat(),
            'word_count': len(content.split()),
            'type': 'course_material'
        }
    
    def scrape_all_content(self):
        """Main scraping function"""
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Get all markdown files
        md_files = self.get_all_markdown_files()
        
        all_content = []
        
        for i, file_path in enumerate(md_files):
            print(f"Processing {i+1}/{len(md_files)}: {file_path}")
            
            content = self.download_file_content(file_path)
            if content:
                processed_content = self.process_markdown_content(content, file_path)
                all_content.append(processed_content)
        
        # Save to JSON file
        output_file = os.path.join(self.data_dir, 'course_content.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_content, f, indent=2, ensure_ascii=False)
        
        print(f"Scraped {len(all_content)} files")
        print(f"Data saved to: {output_file}")
        return all_content

if __name__ == "__main__":
    scraper = TDSCourseScraper()
    content = scraper.scrape_all_content()
    print("Course content scraping completed!")
