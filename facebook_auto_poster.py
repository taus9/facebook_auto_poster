#!/usr/bin/env python3
"""
Facebook Auto Poster
"""

#import time
import logging
import os

#import schedule
from dotenv import load_dotenv

#from facebook_auto_poster_service import FacebookAutoPoster


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="(%(levelname)s)  [%(asctime)s]  %(message)s",
    handlers=[
        logging.FileHandler("facebook_poster.log"),
        logging.StreamHandler()
    ]
)

def load_last_batch() -> list[str]:
    """Loads last_batch.csv and returns contents. If file not found returns an empty list[str]"""
    batch = []
    try:
        with open("last_batch.csv", "r") as file:
            content = file.read()
            batch = content.split(",")
            logging.info("last_batch.csv successfully loaded")
        return batch
    except FileNotFoundError:
        logging.info("last_batch.csv not found")
        return batch

def main():
    """Main function to run the auto poster"""
    page_access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    post_time = os.getenv("POST_TIME", "09:00")
    arrests_api_url = os.getenv("ARRESTS_API_URL", "")

    if not page_access_token or not page_id:
        logging.error("Missing required Facebook credentials. Check your .env file.")
        return

 #   poster = FacebookAutoPoster(
 #       access_token=page_access_token,
 #       page_id=page_id,
 #       arrests_api_url=arrests_api_url
 #   )
    
 #   schedule.every().day.at(post_time).do(poster.scheduled_post)

    logging.info("Facebook Auto Poster started")
    last_batch = load_last_batch()

if __name__ == "__main__":
    main()