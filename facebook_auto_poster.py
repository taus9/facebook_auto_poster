#!/usr/bin/env python3
"""
Facebook Auto Poster - Posts to a Facebook page every 24 hours
Version 2 - Using environment variables for security
"""

import time
import schedule
from datetime import datetime
from facebook import GraphAPI
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('facebook_poster. log'),
        logging.StreamHandler()
    ]
)

class FacebookAutoPoster:
    def __init__(self, access_token, page_id):
        """Initialize the Facebook Auto Poster"""
        self.access_token = access_token
        self.page_id = page_id
        self.graph = GraphAPI(access_token=access_token)
        logging.info("Facebook Auto Poster initialized")
    
    def post_to_page(self, message, link=None, image_path=None):
        """Post content to the Facebook page"""
        try:
            if image_path:
                with open(image_path, 'rb') as image_file:
                    response = self.graph. put_photo(
                        image=image_file,
                        message=message
                    )
            elif link:
                response = self.graph.put_object(
                    parent_object=self.page_id,
                    connection_name='feed',
                    message=message,
                    link=link
                )
            else:
                response = self. graph.put_object(
                    parent_object=self.page_id,
                    connection_name='feed',
                    message=message
                )
            
            logging.info(f"Successfully posted to Facebook. Post ID: {response.get('id', 'N/A')}")
            return response
        
        except Exception as e:
            logging.error(f"Error posting to Facebook: {str(e)}")
            raise
    
    def scheduled_post(self):
        """Method to be called by the scheduler"""
        current_date = datetime.now().strftime("%B %d, %Y")
        message = f"Daily update for {current_date}!  🚀\n\nHave a great day!"
        
        try:
            self. post_to_page(message)
            logging.info("Scheduled post completed successfully")
        except Exception as e:
            logging.error(f"Scheduled post failed:  {str(e)}")


def main():
    """Main function to run the auto poster"""
    # Get configuration from environment variables
    PAGE_ACCESS_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
    PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')
    POST_TIME = os.getenv('POST_TIME', '09:00')
    
    # Validate configuration
    if not PAGE_ACCESS_TOKEN or not PAGE_ID:
        logging.error("Missing required Facebook credentials. Check your .env file.")
        return
    
    # Initialize the poster
    poster = FacebookAutoPoster(
        access_token=PAGE_ACCESS_TOKEN,
        page_id=PAGE_ID
    )
    
    # Schedule the post
    schedule.every().day.at(POST_TIME).do(poster.scheduled_post)
    
    logging.info(f"Facebook Auto Poster started.  Posts scheduled daily at {POST_TIME}")
    logging.info("Press Ctrl+C to stop")
    
    # Keep the script running
    try: 
        while True:
            schedule. run_pending()
            time.sleep(60)
    except KeyboardInterrupt: 
        logging.info("Facebook Auto Poster stopped by user")


if __name__ == "__main__": 
    main()