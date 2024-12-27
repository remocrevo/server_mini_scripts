from flask import render_template, jsonify
import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from datetime import datetime
from . import submissions_bp

load_dotenv()
SUBMITTABLE_API_KEY = os.getenv('SUBMITTABLE_API_KEY')
TIMEOUT = aiohttp.ClientTimeout(total=60)  # 60 second timeout for requests

async def get_session():
    return aiohttp.ClientSession(
        headers={
            'Authorization': f'Basic {SUBMITTABLE_API_KEY}',
            'Content-Type': 'application/json'
        },
        timeout=TIMEOUT
    )

async def get_submissions_page(session, continuation_token=None, size=50):  # Reduced page size
    url = 'https://submittable-api.submittable.com/v4/submissions'
    params = {
        'size': size,
        'continuationToken': continuation_token
    }
    try:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()
    except asyncio.TimeoutError:
        print(f"Timeout getting submissions page with token {continuation_token}")
        return {'items': [], 'continuationToken': None}
    except Exception as e:
        print(f"Error getting submissions page: {str(e)}")
        return {'items': [], 'continuationToken': None}

async def get_reviews(session, submission_id):
    url = f'https://submittable-api.submittable.com/v4/entries/submissions/{submission_id}/reviews'
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()
    except asyncio.TimeoutError:
        print(f"Timeout getting reviews for submission {submission_id}")
        return []
    except Exception as e:
        print(f"Error getting reviews for submission {submission_id}: {str(e)}")
        return []

async def process_submission_batch(session, submissions):
    tasks = []
    for submission in submissions:
        submission_id = submission.get('submissionId')
        if submission_id:
            tasks.append(process_single_submission(session, submission))
    
    if not tasks:
        return []
        
    try:
        return await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        print(f"Error processing submission batch: {str(e)}")
        return []

async def process_single_submission(session, submission):
    try:
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
    except Exception as e:
        print(f"Error processing submission {submission_id}: {str(e)}")
        return None

async def find_submissions_with_two_reviews():
    async with await get_session() as session:
        submissions_with_two_reviews = []
        continuation_token = None
        
        try:
            while True:
                result = await get_submissions_page(session, continuation_token)
                batch_results = await process_submission_batch(session, result.get('items', []))
                
                valid_submissions = [s for s in batch_results if s is not None and not isinstance(s, Exception)]
                submissions_with_two_reviews.extend(valid_submissions)
                
                continuation_token = result.get('continuationToken')
                if not continuation_token:
                    break
                    
            return sorted(submissions_with_two_reviews, 
                         key=lambda x: x['last_review_date'], 
                         reverse=True)
        except Exception as e:
            print(f"Error in find_submissions_with_two_reviews: {str(e)}")
            return []

@submissions_bp.route('/')
async def show_submissions():
    try:
        results = await find_submissions_with_two_reviews()
        return render_template('submission_review/submissions.html', submissions=results)
    except Exception as e:
        return f"Error: {str(e)}", 500
