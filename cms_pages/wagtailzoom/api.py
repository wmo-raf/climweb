from datetime import datetime, timedelta

import jwt
from django.conf import settings
import requests

JWT_EXP_DELTA_SECONDS = 60 * 2  # 2 minutes


class ZoomApi:
    def __init__(self):
        self.is_active = False
        self.headers = {}
        self.base_url = "https://api.zoom.us/v2"
        self.init_api()

    def init_api(self):
        api_key = getattr(settings, 'ZOOM_JWT_API_KEY', '')
        api_secret = getattr(settings, 'ZOOM_JWT_API_SECRET', '')

        payload = {
            'iss': api_key,
            'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
        }

        jwt_token = jwt.encode(payload, api_secret)
        self.headers["Authorization"] = "Bearer {}".format(jwt_token.decode('UTF-8'))

        self.is_active = True

    def _get(self, url):
        headers = {**self.headers}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response

    def _post(self, url, data):
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', **self.headers}
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response

    def get_meeting(self, meeting_id):
        url = "{}/meetings/{}".format(self.base_url, meeting_id)
        response = self._get(url)
        return response.json()

    def get_meeting_questions(self, meeting_id):
        url = "{}/meetings/{}/registrants/questions".format(self.base_url, meeting_id)
        response = self._get(url)
        return response.json()

    def add_meeting_registrant(self, meeting_id, data):
        url = "{}/meetings/{}/registrants".format(self.base_url, meeting_id)
        response = self._post(url, data)
        return response.json()

    def add_webinar_registrant(self, webinar_id, data):
        url = "{}/webinars/{}/registrants".format(self.base_url, webinar_id)
        response = self._post(url, data)
        return response.json()


class ZoomEventsApi:
    def __init__(self):
        self.base_url = "https://events.zoom.us/api/v1"

    def _get(self, url, params=None):
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response

    def get_event_sessions(self, event_id):
        url = f"{self.base_url}/e/v/events/sessions"
        params = {"eventId": event_id}
        response = self._get(url, params)
        return response.json()

    def get_event_speakers(self, event_id):
        url = f"{self.base_url}/e/v/events/speakers"
        params = {"eventId": event_id}
        response = self._get(url, params)
        return response.json()

    def get_event_sponsors(self, event_id):
        url = f"{self.base_url}/e/v/events/sponsors"
        params = {"eventId": event_id}
        response = self._get(url, params)
        return response.json()