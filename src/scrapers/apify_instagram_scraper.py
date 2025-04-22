import requests
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv
import time
import json

class InstagramScraper:
    def __init__(self, db_path='data/project.db'):
        load_dotenv()
        self.api_key = os.getenv('APIFY_API_KEY')
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cur = self.conn.cursor()
        
        sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())

    def convert_timestamp(self, timestamp):
        """Convert various timestamp formats to datetime"""
        if not timestamp:
            return datetime.now()
        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)
        try:
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            return datetime.now()

    def scrape_hashtag_posts(self, hashtag="trump", limit=25):
        """
        Scrape Instagram posts using Apify Instagram Hashtag Scraper
        """
        url = "https://api.apify.com/v2/actor-tasks"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        task_name = f"instagram-hashtag-{int(time.time())}"
        task_data = {
            "actId": "apify/instagram-hashtag-scraper",
            "name": task_name,
            "options": {
                "build": "latest"
            },
            "input": {
                "hashtags": [hashtag],
                "resultsLimit": limit
            }
        }

        try:
            create_task = requests.post(url, headers=headers, json=task_data)
            create_task.raise_for_status()
            task_id = create_task.json()["data"]["id"]
            
            run_url = f"https://api.apify.com/v2/actor-tasks/{task_id}/runs?token={self.api_key}"
            run_response = requests.post(run_url)
            run_response.raise_for_status()
            run_id = run_response.json()["data"]["id"]
            
            dataset_url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items?token={self.api_key}"
            items = []
            
            max_attempts = 30
            attempt = 0
            while attempt < max_attempts:
                response = requests.get(dataset_url)
                if response.status_code == 200:
                    items = response.json()
                    if items:  # If we have results
                        break
                time.sleep(2)
                attempt += 1
                print(f"Waiting for results... attempt {attempt}/{max_attempts}")

            if not items:
                print("No results found after maximum attempts")
                return

            new_posts_count = 0
            for item in items:
                try:
                    # Check if post already exists
                    self.cur.execute('''
                        SELECT id FROM instagram_posts WHERE post_id = ?
                    ''', (item.get('id'),))
                    if self.cur.fetchone():
                        print(f"Skipping duplicate post {item.get('id')}")
                        continue

                    # Insert Instagram post data
                    self.cur.execute('''
                        INSERT INTO instagram_posts 
                        (post_id, username, caption, post_date, likes_count, comments_count, url)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item.get('id'),
                        item.get('ownerFullName'),
                        item.get('caption', ''),
                        self.convert_timestamp(item.get('timestamp')),
                        item.get('likesCount', 0),
                        item.get('commentsCount', 0),
                        item.get('url', '')
                    ))
                    new_posts_count += 1

                except Exception as e:
                    print(f"Error processing item: {e}")
                    print(f"Problematic item: {json.dumps(item, indent=2)}")
                    continue

            self.conn.commit()
            print(f"Successfully scraped {new_posts_count} new Instagram posts")

        except Exception as e:
            print(f"Error during scraping: {e}")
            if hasattr(e, 'response'):
                print(f"Response content: {e.response.content}")

    def close(self):
        """Close database connection"""
        self.conn.close()

if __name__ == "__main__":
    scraper = InstagramScraper()
    try:
        scraper.scrape_hashtag_posts(hashtag="trump", limit=25)
    finally:
        scraper.close() 