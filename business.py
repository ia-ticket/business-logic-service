from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime

AUTH_SERVICE_URL = "http://ia-ticket_auth-service:3000/auth"
IO_SERVICE_URL = 'http://ia-ticket_io-service:5050'

app = Flask(__name__)
CORS(app)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Authorization token is missing'}), 401

        response = requests.post(f'{AUTH_SERVICE_URL}/verify', json={"token": token})
        if response.status_code != 200:
            return jsonify({'message': 'User is not authenticated'}), 401
        
        response_data = response.json()
        email = response_data.get('email')

        if not email:
            return jsonify({'message': 'Email not found in response'}), 401

        request.email = email

        return f(*args, **kwargs)

    return decorated

@app.route('/shows', methods=['GET'])
@token_required
def get_shows():
    headers = {'Authorization': request.headers.get('Authorization')}
    response = requests.get(f'{IO_SERVICE_URL}/shows', headers=headers)

    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({'message': 'Failed to fetch shows'}), response.status_code


@app.route('/my-tickets', methods=['GET'])
@token_required
def get_my_tickets():
    email = request.email
    headers = {'Authorization': request.headers.get('Authorization')}
    response = requests.get(f'{IO_SERVICE_URL}/my-tickets', headers=headers, json={"email": email})

    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({'message': 'Failed to fetch tickets'}), response.status_code
    

@app.route('/tickets-by-show', methods=['GET'])
@token_required
def get_tickets_by_show():
    show_id = request.json.get('show_id')
    headers = {'Authorization': request.headers.get('Authorization')}
    response = requests.get(f'{IO_SERVICE_URL}/tickets-by-show', headers=headers, json={"show_id": show_id})

    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({'message': 'Failed to fetch tickets'}), response.status_code
    

@app.route('/buy-ticket', methods=['PUT'])
@token_required
def buy_ticket():
    data = request.json
    ticket_id = data.get('ticket_id')
    email = request.email
    headers = {'Authorization': request.headers.get('Authorization')}

    ticket = requests.get(f'{IO_SERVICE_URL}/ticket', headers=headers, json={"ticket_id": ticket_id})
    if ticket.status_code == 200:
        show = requests.get(f'{IO_SERVICE_URL}/show', headers=headers, json={"show_id": ticket.json().get('show_id')})
        if show.json().get('inventory') <= 0:
            return jsonify({'message': 'No more tickets are available for this show'}), ticket.status_code
        if ticket.json().get('ticket_status') == 'sold':
            return jsonify({'message': 'Ticket not available'}), ticket.status_code

    response = requests.put(f'{IO_SERVICE_URL}/costumer-email', headers=headers, json={"ticket_id": ticket_id, "email": email})

    if response.status_code == 200:
        response = requests.put(f'{IO_SERVICE_URL}/status', headers=headers, json={"ticket_id": ticket_id, "ticket_status": "sold"})
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            jsonify({'message': 'Failed to buy ticket'}), response.status_code
    else:
        return jsonify({'message': 'Failed to buy ticket'}), response.status_code
    

@app.route('/refund-ticket', methods=['PUT'])
@token_required
def refund_ticket():
    data = request.json
    ticket_id = data.get('ticket_id')
    headers = {'Authorization': request.headers.get('Authorization')}

    current_time = datetime.now()
    ticket = requests.get(f'{IO_SERVICE_URL}/ticket', headers=headers, json={"ticket_id": ticket_id})
    if ticket.status_code == 200:
        if ticket.json().get('ticket_status') == 'available':
            return jsonify({'message': 'Ticket not available for refund'}), ticket.status_code
        show = requests.get(f'{IO_SERVICE_URL}/show', headers=headers, json={"show_id": ticket.json().get('show_id')})
        show_date_and_time_str = show.json().get('date_and_time')
        if datetime.fromisoformat(show_date_and_time_str) < current_time:
            return jsonify({'message': 'Refund period has ended'}), show.status_code
    
    response = requests.put(f'{IO_SERVICE_URL}/status', headers=headers, json={"ticket_id": ticket_id, "ticket_status": "available"})
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({'message': 'Failed to refund ticket'}), response.status_code
    

if __name__ == "__main__":
    app.run(debug=True, port=3500, host='0.0.0.0')
