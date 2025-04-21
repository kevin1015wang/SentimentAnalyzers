import requests
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv
import time
import json

class ApifyRedditScraper:
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

    def scrape_posts(self, search_term="Donald Trump", limit=25):
        """
        Scrape posts using Apify Reddit Scraper Lite
        """
        url = "https://api.apify.com/v2/actor-tasks"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        task_name = f"reddit-search-{int(time.time())}"
        task_data = {
            "actId": "trudax/reddit-scraper-lite",
            "name": task_name,
            "options": {
                "build": "latest"
            },
            "input": {
                "searches": [search_term],
                "maxItems": limit,
                "type": "post",
                "sort": "relevance",
                "time": "all"
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

            for item in items:
                try:
                    self.cur.execute('''
                        INSERT OR IGNORE INTO reddit_users 
                        (username, user_id, karma, account_created, is_moderator, is_verified)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        item.get('username'),
                        item.get('userId'),
                        0,  
                        self.convert_timestamp(item.get('createdAt')),
                        False,  
                        False  
                    ))

                    text_content = f"{item.get('title', '')}\n{item.get('body', '')}"

                    self.cur.execute('''
                        INSERT INTO reddit_posts 
                        (account_name, account_id, post_date, text_content, is_reply, subreddit, upvotes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item.get('username'),
                        item.get('userId'),
                        self.convert_timestamp(item.get('createdAt')),
                        text_content.strip(),
                        False,
                        item.get('parsedCommunityName'),
                        item.get('upVotes', 0)
                    ))

                except Exception as e:
                    print(f"Error processing item: {e}")
                    print(f"Problematic item: {json.dumps(item, indent=2)}")
                    continue

            self.conn.commit()
            print(f"Successfully scraped {len(items)} posts and their users")

        except Exception as e:
            print(f"Error during scraping: {e}")
            if hasattr(e, 'response'):
                print(f"Response content: {e.response.content}")

    def close(self):
        """Close database connection"""
        self.conn.close()

if __name__ == "__main__":
    scraper = ApifyRedditScraper()
    try:
        scraper.scrape_posts()
    finally:
        scraper.close() 