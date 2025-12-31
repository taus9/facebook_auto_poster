# Facebook Arrests Auto Poster

A Python script that fetches recent arrest records from a public API and posts individual updates to the
[Mugs of Lee County Facebook page](https://www.facebook.com/profile.php?id=61585560515914) on a schedule
(via GitHub Actions cron).

Each Facebook post includes a link back to the public booking page on the Mugs site:
https://mugs-site-lee.fly.dev

Related repo for the site: https://github.com/taus9/mugs_site_lee

## How it works

1. Loads required configuration from environment variables.
2. Fetches recent arrest records from a public API endpoint (JSON).
3. Filters out records without images.
4. Filters out records already posted (tracked via `last_batch.csv`).
5. Posts each remaining record to Facebook (photo + message).
6. Writes updated batch + logs back into the repo so the workflow can run fully on GitHub Actions.

## Repo artifacts (intentional)

This project commits a few generated files back into the repo:

- `last_batch.csv` — tracks booking numbers posted in the last run to prevent duplicates
- `facebook_poster.log` — most recent run logs
- `facebook_poster_old.log` — previous run logs (rotated)

This makes the automation “stateful” without needing paid storage.

**Caveat:** because GitHub Actions is committing back into the same repo, the workflow must `git pull`
(or fetch + rebase) before committing to avoid non-fast-forward push errors.

## Requirements

- Python 3.12
- Dependencies in `requirements.txt` (`pip install -r requirements.txt`)
- A Facebook Page access token with permission to publish photos
- A public arrests API endpoint returning booking details and base64-encoded images

## Configuration

The script reads configuration from environment variables:

- `FACEBOOK_PAGE_ACCESS_TOKEN`
- `FACEBOOK_PAGE_ID`
- `ARRESTS_API_URL`
- `MUGS_BOOKING_URL`

For local development you can use a `.env` file.
For GitHub Actions, store these values in **GitHub Secrets**.

## Logging

Logs are written to both stdout and `facebook_poster.log`, including success messages and any errors
returned by the Facebook API.

