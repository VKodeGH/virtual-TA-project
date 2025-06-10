import json

# Load your scraped data
with open("../data/course-content/course_content.json", "r", encoding="utf-8") as f:
    course_data = json.load(f)

with open("../data/discourse-posts/discourse_posts.json", "r", encoding="utf-8") as f:
    discourse_data = json.load(f)

# Sample questions and their keywords (customize these later)
sample_questions = [
    {
        "question": "Should I use gpt-4o-mini which AI proxy supports, or gpt3.5 turbo?",
        "keywords": ["gpt-4o-mini", "gpt3.5 turbo", "AI proxy"]
    },
    {
        "question": "How to count tokens for Japanese text?",
        "keywords": ["token", "count", "Japanese"]
    }
]

# Collect relevant context for each question
context_snippets = []

for q in sample_questions:
    contexts = []
    
    # Search course content
    for course_item in course_data:
        if any(keyword in course_item["content"].lower() for keyword in q["keywords"]):
            contexts.append(course_item["content"][:500])  # First 500 characters
    
    # Search discourse posts
    for post in discourse_data:
        if any(keyword in post["content"].lower() for keyword in q["keywords"]):
            contexts.append(f"{post['content'][:500]} (Source: {post['post_url']})")
    
    # Keep top 5 contexts per question
    context_snippets.append({
        "question": q["question"],
        "contexts": contexts[:5]
    })

# Save to a JSON file
with open("../data/context_snippets.json", "w", encoding="utf-8") as f:
    json.dump(context_snippets, f, indent=2)

print("Context snippets exported to context_snippets.json!")
