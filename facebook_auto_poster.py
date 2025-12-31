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

def rotate_logs():
    new_log = Path("facebook_poster.log")
    old_log = Path("facebook_poster_old.log")

    old_log.unlink(missing_ok=True)

    if new_log.is_file():
        new_log.rename(old_log.name)

def init_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="(%(levelname)s) [%(asctime)s] %(message)s",
        handlers=[
            logging.FileHandler("facebook_poster.log"),
            logging.StreamHandler()
        ]
    )
        
def load_config() -> dict:
    """Load environment variables. Throws exception if required variables are not found."""
    load_dotenv()

    page_access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    arrests_api_url = os.getenv("ARRESTS_API_URL")
    mugs_booking_url = os.getenv("MUGS_BOOKING_URL")

    if not page_access_token or not page_id:
        raise Exception("Missing required Facebook credentials")
        #logging.error("Missing required Facebook credentials. Check your .env file.")
    
    if not arrests_api_url:
        raise Exception("Missing arrest api URL")
    
    if not mugs_booking_url:
        raise Exception("Missing mugs booking URL")
    
    return {
        "page_access_token": page_access_token,
        "page_id": page_id,
        "arrests_api_url": arrests_api_url,
        "mugs_booking_url": mugs_booking_url
    }

def load_last_batch() -> list[str]:
    """Load last_batch.csv and returns contents. If file not found returns an empty list[str]"""
    batch = []
    try:
        with open("last_batch.csv", "r") as file:
            content = file.read()
            batch = content.split(",")
        return batch
    except FileNotFoundError:
        return batch
    except:
        raise

def fetch_recent_arrest(url: str):
    """Retrieve the latest arrest records from the external API"""
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    
    arrests = response.json()

    return arrests

def remove_no_image(arrests):
    """Removes all arrests that do not have an image"""
    new_list = []
    for a in arrests:
        if a["image"]:
            new_list.append(a)

    return new_list

def remove_duplicate(arrests, last_batch):
    """Removes any arrests that may have already been posted"""
    new_list = []
    for a in arrests:
        if a["bookingNumber"] not in last_batch:
            new_list.append(a)

    return new_list

def post_all_arrests(arrests, config):
        index = 1
        new_batch = []
        for a in arrests:
            logging.info(f"attempting to post arrest {index} out of {len(arrests)}...")
            message = build_post_message(a, config["mugs_booking_url"])
            post_to_page(
               config["page_id"], 
                config["page_access_token"],
                message,
                a["bookingNumber"],
                a["image"] 
            )
            new_batch.append(a["bookingNumber"])
            index = index + 1
            break
        return new_batch

def build_post_message(arrest: dict[str, any], mugs_booking_url: str) -> str:
        """Compose the Facebook post message for an individual record"""
        booking_date_full = arrest["bookingDate"]
        
        date_format = '%Y-%m-%d %H:%M:%S.%f'
        booking_date = datetime.strptime(booking_date_full, date_format)
        f_booking_date = booking_date.strftime('%m-%d-%Y %I:%M %p')

        given_name = arrest["givenName"]
        middle_name = arrest["middleName"]
        sur_name = arrest["surName"]

        birth_date_full = arrest["birthDate"]
        birth_date = datetime.strptime(birth_date_full, date_format)

        current_date = datetime.now()
        age = current_date.year - birth_date.year
    
        full_name = ""
        if not middle_name:
            full_name = f"{given_name} {sur_name}"
        else:
            full_name = f"{given_name} {middle_name} {sur_name}"

        booking_url = f"{mugs_booking_url}{arrest["bookingNumber"]}"

        return f"Name: {full_name}\nAge: {age}\nBooked: {f_booking_date}\n\nWhat did they do?? Follow the link for more details.\n{booking_url}"

def post_to_page(page_id, access_token, message: str, booking_number: str, image: str):
        """Post content to the Facebook page"""
        try:
            photo_url = f'https://graph.facebook.com/v24.0/{page_id}/photos'
            image_bytes = base64.b64decode(image)

            files = {
                'source': (f'{booking_number}.jpg', image_bytes, 'image/jpeg')
            }

            data = {
                'published': 'false',
                'access_token': access_token
            }

            response = requests.post(photo_url, files=files, data=data, timeout=15)
            response.raise_for_status()

            try:
                payload = response.json()
            except ValueError:
                payload = {}

            photo_id = payload.get('id') if isinstance(payload, dict) else None
            feed_url = f'https://graph.facebook.com/v24.0/{page_id}/feed'
            data = {
                'message': message,
                'attached_media[0]': '{"media_fbid":"' + photo_id + '"}',
                'access_token': access_token
            }


            response = requests.post(feed_url, data=data)
            response.raise_for_status()

            try:
                payload = response.json()
            except ValueError:
                payload = {}

            #post_id = payload["post_id"]
            post_id = "xxx"
            logging.info("Successfully posted to Facebook. Post ID: %s", post_id or 'N/A')
            return payload

        except Exception as e:
            logging.error(f"Error posting to Facebook: {str(e)}")
            raise

def save_new_batch(new_batch: list[str]):
    batch_str = ",".join(new_batch)
    with open("last_batch.csv", "w") as file:
        file.write(batch_str)
        file.write(",")


def main():
    """Main function to run the auto poster"""
    # I try to write scripts like this in a declarative style
    #
    # 1. Rotate the current log to the old
    # 2. Setup logging config
    # 3. Load environment variables into a config dict
    # 4. Load last batch of arrests booking numbers
    # 5. Fetch recent arrests from public api
    # 6. Remove arrests that don't have an image
    # 7. Remove arrests that are found in the last batch
    # 8. Post remaining arrests to page
    # 9. Save new batch of arrests
    #
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
        logging.info(f"successfully retrieved {len(arrests)} arrest(s)...")

        logging.info("removing arrests with no image...")
        arrests = remove_no_image(arrests)

        logging.info("removing duplicate posts...")
        arrests = remove_duplicate(arrests, last_batch)

        new_batch = post_all_arrests(arrests, config)

        if len(new_batch) != 0:
            save_new_batch(new_batch)
            logging.info("new batch of arrests saved...")

        logging.info("done")        
    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    main()
