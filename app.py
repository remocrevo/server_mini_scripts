# app.py
from flask import Flask, request, render_template, jsonify, send_from_directory
import os
import requests
from dotenv import load_dotenv

# Load API key from environment variable
load_dotenv()
SUBMITTABLE_API_KEY = os.getenv('SUBMITTABLE_API_KEY')

app = Flask(__name__)

# Add route for favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/add-team-member', methods=['POST'])
def add_team_member():
    try:
        email = request.json.get('email')
        if not email:
            return jsonify({'error': 'Email is required'}), 400

        # Add to team
        response = requests.post(
            'https://submittable-api.submittable.com/v4/organizations/team',
            headers={
                'Authorization': f'Basic {SUBMITTABLE_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'emails': [email],
                'permissionLevel': 'Level1',
                'title': 'WM Reviewer, unassigned'
            }
        )

        if response.status_code == 204:
            # Check user status
            team_response = requests.get(
                'https://submittable-api.submittable.com/v4/organizations/team',
                headers={
                    'Authorization': f'Basic {SUBMITTABLE_API_KEY}',
                    'Content-Type': 'application/json'
                }
            )
            
            if team_response.status_code == 200:
                team_data = team_response.json()
                user_id = None
                team_size = len(team_data.get('teamMembers', []))
                
                for member in team_data.get('teamMembers', []):
                    if member.get('email') == email:
                        user_id = member.get('userId')
                        break

                if user_id:
                    if team_size < 175:
                        return jsonify({
                            'status': 'existing_user',
                            'message': 'All set! We will be in touch about your chosen review sessions.'
                        })
                    else:
                        return jsonify({
                            'status': 'team_full',
                            'message': 'Thanks! You won\'t be able to login until your first scheduled review session. Choose a session at VolunteerHub.'
                        })
                else:
                    return jsonify({
                        'status': 'new_user',
                        'message': 'Next, check your email for a confirmation message and create a Submittable account.'
                    })

        elif response.status_code == 400:
            error_data = response.json()
            if error_data.get('messages') and 'already been added to your team' in error_data['messages'][0]:
                return jsonify({
                    'status': 'already_member',
                    'message': 'This email is already associated with a team member.'
                })
            
        return jsonify({'error': 'An unexpected error occurred'}), 500

    except Exception as e:
        app.logger.error(f'Error in add_team_member: {str(e)}')
        return jsonify({'error': 'Server error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=False)
