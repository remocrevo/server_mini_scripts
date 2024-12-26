from flask import render_template, jsonify
import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from datetime import datetime
from . import submissions_bp

# Load environment variables
load_dotenv()
SUBMITTABLE_API_KEY = os.getenv('SUBMITTABLE_API_KEY')

async def get_session():
    return aiohttp.ClientSession(headers={
        'Authorization': f'Basic {SUBMITTABLE_API_KEY}',
        'Content-Type': 'application/json'
    })

async def get_submissions_page(session, continuation_token=None, size=100):
    url = 'https://submittable-api.submittable.com/v4/submissions'
    params = {
        'size': size,
        'continuationToken': continuation_token
    }
    async with session.get(url, params=params) as response:
        response.raise_for_status()
        return await response.json()

async def get_reviews(session, submission_id):
    url = f'https://submittable-api.submittable.com/v4/entries/submissions/{submission_id}/reviews'
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()

async def process_submission_batch(session, submissions):
    tasks = []
    for submission in submissions:
        submission_id = submission.get('submissionId')
        if submission_id:
            tasks.append(process_single_submission(session, submission))
    return await asyncio.gather(*tasks)

async def process_single_submission(session, submission):
    submission_id = submission.get('submissionId')
    reviews = await get_reviews(session, submission_id)
    completed_reviews = [r for r in reviews if r.get('status') == 'completed']
    
    if len(completed_reviews) >= 2:
        return {
            'submission_id': submission_id,
            'title': submission.get('submissionTitle'),
            'status': submission.get('submissionStatus'),
            'review_count': len(completed_reviews),
            'last_review_date': max(r.get('completedAt', '') for r in completed_reviews)
        }
    return None

async def find_submissions_with_two_reviews():
    async with await get_session() as session:
        submissions_with_two_reviews = []
        continuation_token = None
        
        while True:
            result = await get_submissions_page(session, continuation_token)
            batch_results = await process_submission_batch(session, result.get('items', []))
            
            # Filter out None results and add valid submissions
            valid_submissions = [s for s in batch_results if s is not None]
            submissions_with_two_reviews.extend(valid_submissions)
            
            continuation_token = result.get('continuationToken')
            if not continuation_token:
                break
                
        return sorted(submissions_with_two_reviews, 
                     key=lambda x: x['last_review_date'], 
                     reverse=True)

@submissions_bp.route('/')
async def show_submissions():
    try:
        results = await find_submissions_with_two_reviews()
        return render_template('submission_review/submissions.html', submissions=results)
    except Exception as e:
        return f"Error: {str(e)}", 500
