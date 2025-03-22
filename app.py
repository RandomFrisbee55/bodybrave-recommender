from flask import Flask, request, jsonify
import numpy as np
import csv
import logging

app = Flask(__name__)  # Creates your web app

# Logs help us see what’s happening
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load module ratings from a file
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
        MODULES[title] = ratings  # Store ratings for each module
        if int(row['niche']) == 1:
            NICHE_MODULES.append(title)  # Track special interest modules

@app.route('/webhook', methods=['POST'])  # Listens for quiz answers
def process_form():
    logger.debug(f"Headers: {request.headers}")  # Show incoming info
    logger.debug(f"Raw Data: {request.get_data(as_text=True)}")

    # Get quiz answers (tweak IDs later)
    try:
        data = request.json or request.form.to_dict()
        logger.debug(f"Parsed Data: {data}")
    except Exception as e:
        logger.debug(f"Data parsing failed: {e}")
        return jsonify({"error": "Invalid data"}), 400

    goals = [
        int(data.get("q3_understanding", 0)),  # Understanding ED
        int(data.get("q4_emotional", 0)),      # Emotional Resilience
        int(data.get("q5_social", 0)),         # Social Support
        int(data.get("q6_nutrition", 0)),      # Nutrition & Eating
        int(data.get("q7_practical", 0))       # Practical Skills
    ]
    niche_raw = data.get("q8_niche", "")
    niche_selections = niche_raw.split(",") if niche_raw else []

    # Math to pick modules
    total = sum(goals) if sum(goals) > 0 else 1
    weights = [g / total for g in goals]  # How much each goal matters

    results = []
    max_euclidean = np.sqrt(5 * (5**2))  # Max distance for scoring
    for name, ratings in MODULES.items():
        weighted_score = sum(w * r for w, r in zip(weights, ratings))
        normalized_weighted = weighted_score / 5
        euclidean = np.sqrt(sum((g - r) ** 2 for g, r in zip(goals, ratings)))
        normalized_euclidean = (max_euclidean - euclidean) / max_euclidean
        final_score = (0.6 * normalized_weighted) + (0.4 * normalized_euclidean)
        results.append((name, final_score))

    # Pick top 5
    results.sort(key=lambda x: x[1], reverse=True)
    top_modules = [name for name, score in results[:5]]

    # Add special interest modules
    for niche in niche_selections:
        if niche in NICHE_MODULES and niche not in top_modules:
            top_modules.append(niche)

    # Send back as a list
    return jsonify({"recommended_modules": top_modules})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  # Runs locally for testing