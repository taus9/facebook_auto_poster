# Facebook Arrests Auto Poster

This project fetches recent arrest records from a public API and posts individual updates to a Facebook Page on a daily schedule.

## Features
- Loads credentials and schedule configuration from environment variables (see `.env`).
- Retrieves arrest data from an external API, formats the details, and posts one update per record.
- Includes logging to both stdout and a log file for auditing.

## Requirements
- Python 3.12
- Dependencies listed in `requirements.txt` (install with `pip install -r requirements.txt`).
- A Facebook Page access token with permissions to publish photos.
- Public arrests API endpoint providing JSON payloads with booking details and base64-encoded images.

## Usage
1. Create and populate a `.env` file with:
   ```ini
   FACEBOOK_PAGE_ACCESS_TOKEN=your_token
   FACEBOOK_PAGE_ID=your_page_id
   POST_TIME=09:00
   ARRESTS_API_URL=https://www.sheriffleefl.org/public-api/bookings
   ```
2. Activate the virtual environment (`source .venv/bin/activate`) or use the provided interpreter path.
3. Run the scheduled poster:
   ```bash
   python3 facebook_auto_poster.py
   ```
   Or as a service:
   ```bash
   nohup python3 facebook_auto_poster.py &
   ```

## Logging
Outputs are written to both the console and `facebook_poster.log`, capturing successes and any errors returned by the Facebook API.
