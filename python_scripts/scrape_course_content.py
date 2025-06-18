import re
import os
import json
import time
from pathlib import Path
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

# ========== CONFIGURATION ==========
# Set up Gemini API key from environment variable
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ========== PATH SETUP ==========
# Get the root directory (parent of python-scripts)
ROOT_DIR = Path(__file__).resolve().parent.parent

# Path to the cloned repo
REPO_PATH = ROOT_DIR / 'tools-in-data-science-public'

# Output directory and file
OUTPUT_DIR = ROOT_DIR / 'data' / 'course-content'
OUTPUT_FILE = OUTPUT_DIR / 'course_content.json'

# ========== IMAGE DESCRIPTION CACHE ==========
# Optional: cache Gemini responses to avoid duplicate requests
CACHE_FILE = ROOT_DIR / 'data' / 'image_descriptions_cache.json'
if CACHE_FILE.exists():
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        image_cache = json.load(f)
else:
    image_cache = {}

def describe_image(alt_text, image_url):
    """Get or generate a Gemini description for an image."""
    cache_key = f"{alt_text}|{image_url}"
    if cache_key in image_cache:
        return image_cache[cache_key]
    try:
        prompt = f"Describe this educational image in detail for student assistance. Alt text: '{alt_text}'."
        response = model.generate_content(prompt)
        description = response.text.strip()
        image_cache[cache_key] = description
        # Save cache after every new description
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(image_cache, f, indent=2, ensure_ascii=False)
        time.sleep(1)  # Rate limit
        return description
    except Exception as e:
        return f"Image description unavailable: {str(e)}"

def process_markdown(file_path, repo_root):
    """Process markdown file: replace images with Gemini descriptions."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex for Markdown images: ![alt](url)
    image_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
    images = image_pattern.findall(content)

    # Replace images with Gemini descriptions
    def replace_image(match):
        alt_text = match.group(1)
        image_url = match.group(2)
        description = describe_image(alt_text, image_url)
        return f"[Image Description: {description}]"

    processed_content = image_pattern.sub(replace_image, content)

    # Build correct GitHub URL (handles subdirectories)
    relative_path = file_path.relative_to(repo_root)
    github_url = f"https://github.com/sanand0/tools-in-data-science-public/blob/main/{relative_path.as_posix()}"

    return {
        "file_path": str(relative_path),
        "github_url": github_url,
        "content": processed_content,
        "word_count": len(processed_content.split()),
        "image_urls": [img[1] for img in images],
        "processed_at": datetime.now().isoformat()
    }

def main():
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    processed_files = []

    for md_file in REPO_PATH.glob('**/*.md'):
        # Skip README.md and config files
        if md_file.name.lower() == 'readme.md':
            continue
        processed = process_markdown(md_file, REPO_PATH)
        processed_files.append(processed)
        print(f"Processed: {md_file}")

    # Save all processed content to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(processed_files, f, indent=2, ensure_ascii=False)
    print(f"\nAll done! Output saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
