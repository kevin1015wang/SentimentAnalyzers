import os
from dotenv import load_dotenv
from scrapers.apify_instagram_scraper import InstagramScraper
from scrapers.reddit_scraper import ApifyRedditScraper
from database_setup import create_tables

load_dotenv()

def main():
    create_tables()
    
    instagram_scraper = InstagramScraper()
    reddit_scraper = ApifyRedditScraper()
    
    try:
        print("\nScraping Instagram posts...")
        instagram_scraper.scrape_hashtag_posts(hashtag="trump", limit=25)
        
        print("\nScraping Reddit posts...")
        reddit_scraper.scrape_posts(search_term="Donald Trump", limit=25)
    finally:
        instagram_scraper.close()
        reddit_scraper.close()

if __name__ == '__main__':
    main()