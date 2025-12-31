#!/usr/bin/env python3
"""
Facebook Auto Poster
"""

import base64
import os
import logging
import requests

from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv


LOG_NEW = Path("facebook_poster.log")
LOG_OLD = Path("facebook_poster_old.log")
BATCH_FILE = Path("last_batch.csv")


def rotate_logs():
    LOG_OLD.unlink(missing_ok=True)
    if LOG_NEW.is_file():
        LOG_NEW.rename(LOG_OLD)


def init_logger():
    # If you ever call init_logger() more than once in the same process,
    # basicConfig won't reconfigure unless you pass force=True (py3.8+).
    logging.basicConfig(
        level=logging.INFO,
        format="(%(levelname)s) [%(asctime)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_NEW),
            logging.StreamHandler()
        ]
    )


def load_config() -> dict:
    """Load environment variables. Throws if required variables are not found."""
    load_dotenv()

    config = {
        "page_access_token": os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN"),
        "page_id": os.getenv("FACEBOOK_PAGE_ID"),
        "arrests_api_url": os.getenv("ARRESTS_API_URL"),
        "mugs_booking_url": os.getenv("MUGS_BOOKING_URL"),
    }

    missing = [k for k, v in config.items() if not v]
    if missing:
        raise Exception(f"Missing required env vars: {', '.join(missing)}")

    return config


def load_last_batch() -> list[str]:
    """Load last_batch.csv contents. If file not found returns an empty list."""
    if not BATCH_FILE.exists():
        return []

    content = BATCH_FILE.read_text().strip()
    if not content:
        return []

    # Split + remove empty strings (handles trailing commas safely)
    return [x for x in content.split(",") if x]


def fetch_recent_arrest(url: str) -> list[dict]:
    """Retrieve the latest arrest records from the external API"""
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


def remove_no_image(arrests: list[dict]) -> list[dict]:
    """Removes all arrests that do not have an image"""
    return [a for a in arrests if a.get("image")]


def remove_duplicate(arrests: list[dict], last_batch: list[str]) -> list[dict]:
    """Removes any arrests that may have already been posted"""
    last = set(last_batch)
    return [a for a in arrests if a.get("bookingNumber") not in last]


def post_all_arrests(arrests: list[dict], config: dict) -> list[str]:
    new_batch: list[str] = []
    total = len(arrests)

    for idx, a in enumerate(arrests, start=1):
        logging.info("attempting to post arrest %s out of %s...", idx, total)

        message = build_post_message(a, config["mugs_booking_url"])
        post_to_page(
            config["page_id"],
            config["page_access_token"],
            message,
            a["bookingNumber"],
            a["image"],
        )
        new_batch.append(a["bookingNumber"])
        
    return new_batch


def _calc_age(birth_date: datetime, now: datetime) -> int:
    years = now.year - birth_date.year
    if (now.month, now.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def build_post_message(arrest: dict, mugs_booking_url: str) -> str:
    """Compose the Facebook post message for an individual record"""
    date_format = "%Y-%m-%d %H:%M:%S.%f"

    booking_date = datetime.strptime(arrest["bookingDate"], date_format)
    f_booking_date = booking_date.strftime("%m-%d-%Y %I:%M %p")

    given_name = arrest.get("givenName", "").strip()
    middle_name = (arrest.get("middleName") or "").strip()
    sur_name = arrest.get("surName", "").strip()

    birth_date = datetime.strptime(arrest["birthDate"], date_format)
    age = _calc_age(birth_date, datetime.now())

    if middle_name:
        full_name = f"{given_name} {middle_name} {sur_name}".strip()
    else:
        full_name = f"{given_name} {sur_name}".strip()

    booking_number = arrest["bookingNumber"]
    booking_url = f"{mugs_booking_url}{booking_number}"

    return (
        f"Name: {full_name}\n"
        f"Age: {age}\n"
        f"Booked: {f_booking_date}\n\n"
        f"What did they do?? Follow the link for more details.\n"
        f"{booking_url}"
    )


def post_to_page(page_id: str, access_token: str, message: str, booking_number: str, image: str) -> dict:
    """Post content to the Facebook page"""
    try:
        photo_url = f"https://graph.facebook.com/v24.0/{page_id}/photos"
        image_bytes = base64.b64decode(image)

        files = {
            "source": (f"{booking_number}.jpg", image_bytes, "image/jpeg")
        }

        # Upload unpublished photo
        data = {"published": "false", "access_token": access_token}
        r = requests.post(photo_url, files=files, data=data, timeout=15)
        r.raise_for_status()
        payload = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}

        photo_id = payload.get("id")
        if not photo_id:
            raise Exception(f"Facebook photo upload did not return an id. Response: {payload}")

        # Create feed post with attached media
        feed_url = f"https://graph.facebook.com/v24.0/{page_id}/feed"
        data = {
            "message": message,
            "attached_media[0]": f'{{"media_fbid":"{photo_id}"}}',
            "access_token": access_token,
        }

        r = requests.post(feed_url, data=data, timeout=15)
        r.raise_for_status()
        payload = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}

        post_id = payload.get("id") or payload.get("post_id")
        logging.info("Successfully posted to Facebook. Post ID: %s", post_id or "N/A")
        return payload

    except Exception as e:
        logging.error("Error posting to Facebook: %s", str(e))
        raise


def save_new_batch(new_batch: list[str]):
    # No trailing comma
    BATCH_FILE.write_text(",".join(new_batch))


def main():
    """Main function to run the auto poster"""
    try:
        rotate_logs()
        init_logger()

        logging.info("Facebook Auto Poster started")

        config = load_config()
        logging.info("config loaded successfully...")

        last_batch = load_last_batch()
        logging.info("last_batch.csv successfully loaded...")

        logging.info("attempting to fetch recent arrests...")
        arrests = fetch_recent_arrest(config["arrests_api_url"])
        logging.info("successfully retrieved %s arrest(s)...", len(arrests))

        logging.info("removing arrests with no image...")
        arrests = remove_no_image(arrests)

        logging.info("removing duplicate posts...")
        arrests = remove_duplicate(arrests, last_batch)

        new_batch = post_all_arrests(arrests, config)

        if new_batch:
            save_new_batch(new_batch)
            logging.info("new batch of arrests saved...")

        logging.info("done")

    except Exception as e:
        logging.exception("Fatal error: %s", e)


if __name__ == "__main__":
    main()
