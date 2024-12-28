from flask import render_template, jsonify
import os
import asyncio
from asyncio import Semaphore, sleep
import aiohttp
from dotenv import load_dotenv
import logging
from datetime import datetime
from . import submissions_bp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
SUBMITTABLE_API_KEY = os.getenv('SUBMITTABLE_API_KEY')
TIMEOUT = aiohttp.ClientTimeout(total=60)

RATE_LIMIT = 1  # Maximum number of requests per second (adjust per API documentation)

async def rate_limited_request(task, *args, semaphore=None, **kwargs):
    if semaphore:
        async with semaphore:
            try:
                result = await task(*args, **kwargs)
                await sleep(1 / RATE_LIMIT)  # Introduce delay to adhere to rate limits
                return result
            except Exception as e:
                logger.error(f"Rate-limited request failed: {str(e)}")
                raise
    else:
        return await task(*args, **kwargs)

async def get_session():
    logger.info("Creating new session")
    return aiohttp.ClientSession(
        headers={
            'Authorization': f'Basic {SUBMITTABLE_API_KEY}',
            'Content-Type': 'application/json'
        },
        timeout=TIMEOUT
    )

async def get_submissions_page(session, continuation_token=None, size=50):
    semaphore = Semaphore(RATE_LIMIT)
    
    async def task():
        url = 'https://submittable-api.submittable.com/v4/submissions'
        params = {'size': size}
        if continuation_token is not None:
            params['continuationToken'] = continuation_token

        try:
            logger.info(f"Fetching submissions page with token: {continuation_token}")
            async with session.get(url, params=params) as response:
                if response.status == 401:
                    logger.error("Authentication failed - check your API key")
                    return {'items': [], 'continuationToken': None}
                response.raise_for_status()
                return await response.json()

        except asyncio.TimeoutError:
            logger.error(f"Timeout getting submissions page with token {continuation_token}")
            return {'items': [], 'continuationToken': None}
        except Exception as e:
            logger.error(f"Error getting submissions page: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            return {'items': [], 'continuationToken': None}

    return await rate_limited_request(task, semaphore=semaphore)

async def get_reviews(session, submission_id):
    semaphore = Semaphore(RATE_LIMIT)
    
    async def task():
        url = f'https://submittable-api.submittable.com/v4/entries/submissions/{submission_id}/reviews'

        try:
            logger.info(f"Fetching reviews for submission {submission_id}")
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting reviews for submission {submission_id}")
            return []
        except Exception as e:
            logger.error(f"Error getting reviews for submission {submission_id}: {str(e)}")
            return []

    return await rate_limited_request(task, semaphore=semaphore)

async def process_submission_batch(session, submissions):
    logger.info(f"Processing batch of {len(submissions)} submissions")
    tasks = []
    for submission in submissions:
        submission_id = submission.get('submissionId')
        if submission_id:
            tasks.append(process_single_submission(session, submission))
    
    if not tasks:
        return []
        
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        logger.info(f"Processed batch: {len(valid_results)} valid results out of {len(results)} total")
        return valid_results
    except Exception as e:
        logger.error(f"Error processing submission batch: {str(e)}")
        return []

async def process_single_submission(session, submission):
    submission_id = submission.get('submissionId')
    try:
        logger.info(f"Processing submission {submission_id}")
        reviews = await get_reviews(session, submission_id)
        completed_reviews = [r for r in reviews if r.get('status') == 'completed']
        
        if len(completed_reviews) >= 2:
            logger.info(f"Submission {submission_id} has {len(completed_reviews)} completed reviews")
            return {
                'submission_id': submission_id,
                'title': submission.get('submissionTitle'),
                'status': submission.get('submissionStatus'),
                'review_count': len(completed_reviews),
                'last_review_date': max(r.get('completedAt', '') for r in completed_reviews)
            }
        logger.info(f"Submission {submission_id} only has {len(completed_reviews)} completed reviews")
        return None
    except Exception as e:
        logger.error(f"Error processing submission {submission_id}: {str(e)}")
        return None

async def find_submissions_with_two_reviews():
    logger.info("Starting to find submissions with two reviews")
    semaphore = Semaphore(RATE_LIMIT)
    
    async with await get_session() as session:
        submissions_with_two_reviews = []
        continuation_token = None
        
        try:
            page_count = 0
            while True:
                page_count += 1
                logger.info(f"Fetching page {page_count}")
                result = await rate_limited_request(get_submissions_page, session, continuation_token, semaphore=semaphore)
                if not result.get('items'):
                    logger.warning("No items received in response")
                    break
                    
                batch_results = await process_submission_batch(session, result.get('items', []))
                submissions_with_two_reviews.extend(batch_results)
                
                continuation_token = result.get('continuationToken')
                logger.info(f"Current submissions count: {len(submissions_with_two_reviews)}")
                if not continuation_token:
                    logger.info("No more pages to fetch")
                    break
                    
            logger.info(f"Found total of {len(submissions_with_two_reviews)} submissions with 2+ reviews")
            return sorted(submissions_with_two_reviews, 
                         key=lambda x: x['last_review_date'], 
                         reverse=True)
        except Exception as e:
            logger.error(f"Error in find_submissions_with_two_reviews: {str(e)}")
            return []

@submissions_bp.route('/')
async def show_submissions():
    try:
        logger.info("Starting show_submissions route")
        # Print the API key length to debug (don't print the actual key!)
        if SUBMITTABLE_API_KEY:
            logger.info(f"API key is present (length: {len(SUBMITTABLE_API_KEY)})")
        else:
            logger.error("No API key found!")
            
        results = await find_submissions_with_two_reviews()
        logger.info(f"Rendering template with {len(results)} submissions")
        return render_template('submission_review/submissions.html', submissions=results)
    except Exception as e:
        logger.error(f"Error in show_submissions: {str(e)}")
        return f"Error: {str(e)}", 500
