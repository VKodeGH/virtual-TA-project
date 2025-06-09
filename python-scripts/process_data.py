import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

# Load scraped data
with open("../data/course-content/course_content.json", "r", encoding='utf-8') as f:
    course_data = json.load(f)

with open("../data/discourse-posts/discourse_posts.json", "r", encoding='utf-8') as f:
    discourse_data = json.load(f)

# Combine data into a single list of documents
documents = []
for item in course_data:
    documents.append({
        "text": item["content"],
        "source": "course",
        "metadata": item["file_path"]
    })

for post in discourse_data:
    documents.append({
        "text": post["content"],
        "source": "discourse",
        "metadata": post["post_url"]
    })

# Create TF-IDF vectorizer (simple keyword-based search)
vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform([doc["text"] for doc in documents])

# Save processed data
processed_data = {
    "documents": documents,
    "vectorizer": vectorizer,
    "tfidf_matrix": tfidf_matrix
}

with open("../data/processed_data.pkl", "wb") as f:
    import pickle
    pickle.dump(processed_data, f)

print("Data processed and saved!")
