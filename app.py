from flask import Flask, request, jsonify
import numpy as np
import csv
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load modules from CSV
MODULES = {}
NICHE_MODULES = []
with open('modules.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        title = row['Title']
        ratings = [
            int(row['Understanding ED']),
            int(row['Emotional Resilience']),
            int(row['Social Support']),
            int(row['Nutrition & Eating']),
            int(row['Practical Skills'])
        ]
        MODULES[title] = ratings
        if int(row['niche']) == 1:
            NICHE_MODULES.append(title)

@app.route('/webhook', methods=['POST'])
def process_form():
    # Log request details
    logger.debug(f"Headers: {request.headers}")
    logger.debug(f"Raw Data: {request.get_data(as_text=True)}")

    # Handle both JSON and form data
    try:
        data = request.json
        logger.debug(f"Parsed JSON: {data}")
    except Exception as e:
        logger.debug(f"JSON parsing failed: {e}")
        data = request.form.to_dict()
        logger.debug(f"Parsed Form Data: {data}")

    # Extract goals (adjust field IDs based on your JotForm payload)
    goals = [
        int(data.get("q1", 0)),  # Understanding ED
        int(data.get("q2", 0)),  # Emotional Resilience
        int(data.get("q3", 0)),  # Social Support
        int(data.get("q4", 0)),  # Nutrition & Eating
        int(data.get("q5", 0))   # Practical Skills
    ]
    # Extract niche selections
    niche_raw = data.get("q6", "")
    niche_selections = niche_raw.split(",") if niche_raw else []

    # Calculate weights
    total = sum(goals) if sum(goals) > 0 else 1
    weights = [g / total for g in goals]

    # Compute scores
    results = []
    max_euclidean = np.sqrt(5 * (5**2))  # ≈ 11.18
    for name, ratings in MODULES.items():
        weighted_score = sum(w * r for w, r in zip(weights, ratings))
        normalized_weighted = weighted_score / 5
        euclidean = np.sqrt(sum((g - r) ** 2 for g, r in zip(goals, ratings)))
        normalized_euclidean = (max_euclidean - euclidean) / max_euclidean
        final_score = (0.6 * normalized_weighted) + (0.4 * normalized_euclidean)
        results.append((name, final_score))

    # Top 5 modules
    results.sort(key=lambda x: x[1], reverse=True)
    top_modules = [name for name, score in results[:5]]

    # Add niche modules
    for niche in niche_selections:
        if niche in NICHE_MODULES and niche not in top_modules:
            top_modules.append(niche)

    # Return JSON for JotForm Thank You Page
    return jsonify({"recommended_modules": top_modules})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

