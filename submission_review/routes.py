# submission_review/routes.py
from flask import render_template
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from . import submissions_bp

# Load environment variables
load_dotenv()
SUBMITTABLE_API_KEY = os.getenv('SUBMITTABLE_API_KEY')

def get_submissions(continuation_token=None, size=500):
    url = 'https://submittable-api.submittable.com/v4/submissions'
    headers = {
        'Authorization': f'Basic {SUBMITTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    params = {
        'size': size,
        'continuationToken': continuation_token
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def get_reviews(submission_id):
    url = f'https://submittable-api.submittable.com/v4/entries/submissions/{submission_id}/reviews'
    headers = {
        'Authorization': f'Basic {SUBMITTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def find_submissions_with_two_reviews():
    submissions_with_two_reviews = []
    continuation_token = None

    while True:
        result = get_submissions(continuation_token)

        for submission in result.get('items', []):
            submission_id = submission.get('submissionId')
            if not submission_id:
                continue

            reviews = get_reviews(submission_id)
            completed_reviews = [r for r in reviews if r.get('status') == 'completed']

            if len(completed_reviews) >= 2:
                submissions_with_two_reviews.append({
                    'submission_id': submission_id,
                    'title': submission.get('submissionTitle'),
                    'status': submission.get('submissionStatus'),
                    'review_count': len(completed_reviews),
                    'last_review_date': max(r.get('completedAt', '') for r in completed_reviews)
                })

        continuation_token = result.get('continuationToken')
        if not continuation_token:
            break

    return sorted(submissions_with_two_reviews, key=lambda x: x['last_review_date'], reverse=True)

@submissions_bp.route('/')
def show_submissions():
    try:
        results = find_submissions_with_two_reviews()
        return render_template('submissions.html', submissions=results)
    except Exception as e:
        return f"Error: {str(e)}", 500
