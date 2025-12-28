#!/usr/bin/env python3
"""
Facebook Auto Poster
"""

import os
import logging

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="(%(levelname)s)  [%(asctime)s]  %(message)s",
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

    if not page_access_token or not page_id:
        raise Exception("Missing required Facebook credentials")
        #logging.error("Missing required Facebook credentials. Check your .env file.")
    
    if not arrests_api_url:
        raise Exception("Missing arrest api URL")
    
    return {
        "page_access_token": page_access_token,
        "page_id": page_id,
        "arrests_api_url": arrests_api_url,
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

def main():
    """Main function to run the auto poster"""
    logging.info("Facebook Auto Poster started")
    try:
        config = load_config()
        logging.info("config loaded successfully...")

        last_batch = load_last_batch()
        logging.info("last_batch.csv successfully loaded...")
        
    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    main()