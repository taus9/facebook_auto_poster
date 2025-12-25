#!/usr/bin/env python3
"""
Facebook Auto Poster - Posts to a Facebook page every 24 hours
"""

import time
import schedule
from datetime import datetime
from facebook import GraphAPI
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging. FileHandler('facebook_poster.log'),
        logging.StreamHandler()
    ]
)

class FacebookAutoPoster:
    def __init__(self, access_token, page_id):
        """
        Initialize the Facebook Auto Poster
        
        Args:
            access_token (str): Facebook Page Access Token
            page_id (str): Facebook Page ID
        """
        self.access_token = access_token
        self.page_id = page_id
        self.graph = GraphAPI(access_token=access_token)
        logging.info("Facebook Auto Poster initialized")
    
    def post_to_page(self, message, link=None, image_path=None):
        """
        Post content to the Facebook page
        
        Args:
            message (str): The message to post
            link (str, optional): URL to share
            image_path (str, optional): Path to image file to upload
        
        Returns:
            dict: Response from Facebook API
        """
        try:
            if image_path:
                # Post with photo
                with open(image_path, 'rb') as image_file:
                    response = self.graph.put_photo(
                        image=image_file,
                        message=message
                    )
            elif link:
                # Post with link
                response = self.graph. put_object(
                    parent_object=self.page_id,
                    connection_name='feed',
                    message=message,
                    link=link
                )
            else:
                # Post text only
                response = self.graph.put_object(
                    parent_object=self.page_id,
                    connection_name='feed',
                    message=message
                )
            
            logging.info(f"Successfully posted to Facebook.  Post ID: {response.get('id', 'N/A')}")
            return response
        
        except Exception as e: 
            logging.error(f"Error posting to Facebook: {str(e)}")
            raise
    
    def scheduled_post(self):
        """
        Method to be called by the scheduler
        Customize this method with your posting logic
        """
        # Customize your message here
        current_date = datetime.now().strftime("%B %d, %Y")
        message = f"Daily update for {current_date}!  🚀\n\nHave a great day!"
        
        try:
            self.post_to_page(message)
            logging.info("Scheduled post completed successfully")
        except Exception as e:
            logging. error(f"Scheduled post failed: {str(e)}")


def main():
    """
    Main function to run the auto poster
    """
    # ============================================================
    # CONFIGURATION - Replace with your actual values
    # ============================================================
    PAGE_ACCESS_TOKEN = "YOUR_PAGE_ACCESS_TOKEN_HERE"
    PAGE_ID = "YOUR_PAGE_ID_HERE"
    
    # Initialize the poster
    poster = FacebookAutoPoster(
        access_token=PAGE_ACCESS_TOKEN,
        page_id=PAGE_ID
    )
    
    # Schedule the post to run every 24 hours at a specific time
    # Adjust the time as needed (24-hour format)
    schedule.every().day.at("09:00").do(poster.scheduled_post)
    
    # Alternative: Run every 24 hours from when the script starts
    # schedule. every(24).hours.do(poster.scheduled_post)
    
    logging.info("Facebook Auto Poster started.  Waiting for scheduled posts...")
    logging.info("Press Ctrl+C to stop")
    
    # Optional: Make an immediate test post
    # poster.scheduled_post()
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logging.info("Facebook Auto Poster stopped by user")


if __name__ == "__main__":
    main()