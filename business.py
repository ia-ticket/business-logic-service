from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

AUTH_SERVICE_URL = "http://auth:3000/auth"
IO_SERVICE_URL = 'http://io:5050'

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


if __name__ == "__main__":
    app.run(debug=True, port=3500, host='0.0.0.0')
