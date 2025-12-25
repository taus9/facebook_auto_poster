"""
Configuration file for Facebook Auto Poster
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Facebook credentials
PAGE_ACCESS_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')

# Posting schedule (24-hour format)
POST_TIME = os.getenv('POST_TIME', '09:00')

# Validate configuration
if not PAGE_ACCESS_TOKEN or not PAGE_ID:
    raise ValueError("Missing required Facebook credentials.  Check your .env file.")