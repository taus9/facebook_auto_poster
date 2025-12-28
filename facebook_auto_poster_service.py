import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import base64
import requests

class FacebookAutoPoster:
    def __init__(
        self,
        access_token: str,
        page_id: str,
        arrests_api_url: str,
        http_timeout: int = 15,
        post_delay: int = 2,
        max_posts: int = 20,
        http_session: Optional[requests.Session] = None,
    ):
        """Initialize the Facebook Auto Poster"""
        self.access_token = access_token
        self.page_id = page_id
        self.arrests_api_url = arrests_api_url
        self.http_timeout = http_timeout
        self.post_delay = post_delay
        self.max_posts = max_posts if max_posts and max_posts > 0 else 3
        self.http = http_session or requests.Session()
        logging.info("Facebook Auto Poster initialized")

    def fetch_recent_arrests(self) -> List[Dict[str, Any]]:
        """Retrieve the latest arrest records from the external API"""
        if not self.arrests_api_url:
            logging.error("Arrests API URL missing; skipping fetch")
            return []

        try:
            response = self.http.get(self.arrests_api_url, timeout=self.http_timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            logging.error("Failed to retrieve arrest records: %s", exc)
            return []

        try:
            payload = response.json()
        except ValueError as exc:
            logging.error("Arrests API did not return valid JSON: %s", exc)
            return []

        if isinstance(payload, dict):
            records = payload.get('results') or payload.get('data') or []
        else:
            records = payload

        if not isinstance(records, list):
            logging.error("Unexpected arrests payload structure; expected list, got %s", type(records).__name__)
            return []

        return [record for record in records if isinstance(record, dict)]

    def build_post_message(self, record: Dict[str, Any]) -> str:
        """Compose the Facebook post message for an individual record"""
        booking_date_full = record.get('bookingDate')
        
        date_format = '%Y-%m-%d %H:%M:%S.%f'
        booking_date = datetime.strptime(booking_date_full, date_format)
        f_booking_date = booking_date.strftime('%m-%d-%Y %I:%M %p')

        given_name = record.get('givenName')
        middle_name = record.get('middleName')
        sur_name = record.get('surName')

        birth_date_full = record.get('birthDate')
        birth_date = datetime.strptime(birth_date_full, date_format)

        current_date = datetime.now()
        age = current_date.year - birth_date.year

        full_name = ""
        if not middle_name:
            full_name = f"{given_name} {sur_name}"
        else:
            full_name = f"{given_name} {middle_name} {sur_name}"

        return f"Name: {full_name}\nAge: {age}\nBooked: {f_booking_date}"

    def post_to_page(self, message: str, record_id: str, image_b64: str):
        """Post content to the Facebook page"""
        try:
            url = f'https://graph.facebook.com/v24.0/{self.page_id}/photos'
            image_bytes = base64.b64decode(image_b64)

            files = {
                'source': (f'{record_id}.jpg', image_bytes, 'image/jpeg')
            }

            data = {
                'caption': message,
                'access_token': self.access_token
            }

            response = self.http.post(url, files=files, data=data, timeout=self.http_timeout)
            response.raise_for_status()

            try:
                payload = response.json()
            except ValueError:
                payload = {}

            post_id = payload.get('id') if isinstance(payload, dict) else None
            logging.info("Successfully posted to Facebook. Post ID: %s", post_id or 'N/A')
            return payload

        except Exception as e:
            logging.error(f"Error posting to Facebook: {str(e)}")
            raise

    def scheduled_post(self):
        """Method to be called by the scheduler"""
        records = self.fetch_recent_arrests()

        if not records:
            logging.info("No arrest records fetched; skipping scheduled posts")
            return

        limit = min(len(records), self.max_posts)
        for index, record in enumerate(records[:limit], start=1):
            message = self.build_post_message(record)
            
            record_id = record.get('id')
            image = record.get('image')

            if not image:
                logging.info("Skipping record: No Image")
                continue
            if not record_id:
                logging.info("Skipping record: Missing id")
                continue

            try:
                self.post_to_page(message, record_id, image)
                logging.info("Posted arrest record %s/%s", index, limit)
            except Exception as exc:
                logging.error("Failed to post arrest record %s: %s", index, exc)
            time.sleep(self.post_delay)