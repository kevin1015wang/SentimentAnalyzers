from __future__ import annotations
import os
from dotenv import load_dotenv

# Project
from src.database_setup import create_tables
from src.scrapers.apify_instagram_scraper import InstagramScraper
from src.scrapers.reddit_scraper        import ApifyRedditScraper

from src.processing.sentiment_analyzer  import main as sentiment_main
from src.processing.process_data        import main as process_data_main
from src.processing.user_age_analysis   import analyze_account_age_sentiment
from visuals.plot_sentiment             import main as plot_sentiment_main

# Scraper helper
def run_scrapers() -> None:
    """Scrape 25 fresh posts from each platform."""
    insta = InstagramScraper()
    reddit = ApifyRedditScraper()
    try:
        print("\n Scraping Instagram (#trump)…")
        insta.scrape_hashtag_posts(hashtag="trump", api_limit=150, db_limit=25)

        print("\n Scraping Reddit (Donald Trump)…")
        reddit.scrape_posts(search_term="Donald Trump", api_limit=150, db_limit=25)
    finally:
        insta.close()
        reddit.close()

# Main
def main() -> None:
    load_dotenv()
    create_tables()

    # scrape
    run_scrapers()

    # sentiment score
    print("\nSentiment analysis…")
    sentiment_main()

    # account age analysis
    print("\nAnalyzing account age and sentiment…")
    analyze_account_age_sentiment()

    # generate calculation files
    print("\nBuilding calculation files…")
    process_data_main()

    # create plots
    print("\nRendering plots…")
    plot_sentiment_main()

    print("\nDone! Check the data/ and visuals/ folders")

# ───────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()