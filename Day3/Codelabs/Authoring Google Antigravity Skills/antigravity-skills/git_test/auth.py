# Copyright (c) 2026 MyCompany LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.oauth2 import id_token
from google.auth.transport import requests

CLIENT_ID = "YOUR_CLIENT_ID.apps.googleusercontent.com"

def login():
    pass

def login_with_google(token: str):
    """Verifies a Google ID token and returns the user's information if valid."""
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
        return {
            "status": "success",
            "user_id": idinfo['sub'],
            "email": idinfo.get('email'),
            "name": idinfo.get('name')
        }
    except ValueError:
        return {
            "status": "error",
            "message": "Invalid token"
        }

