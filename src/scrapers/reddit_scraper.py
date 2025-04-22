import requests
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv
import time
import json
import random

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

    def scrape_posts(self, search_term="Donald Trump", api_limit=150, db_limit=25):
        """
        Scrape posts using Apify Reddit Scraper Lite
        
        Args:
            search_term: Term to search for
            api_limit: Number of results to fetch from API (default: 150)
            db_limit: Maximum number of new posts to add to database (default: 25)
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
                "maxItems": api_limit,
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
            
            max_attempts = 60  # Increased from 30 to 60
            attempt = 0
            last_count = 0
            no_new_items_count = 0
            
            while attempt < max_attempts:
                response = requests.get(dataset_url)
                if response.status_code == 200:
                    current_items = response.json()
                    if current_items:  # If we have results
                        if len(current_items) > len(items):
                            items = current_items
                            last_count = len(items)
                            no_new_items_count = 0
                            print(f"Found {len(items)} items so far...")
                        else:
                            no_new_items_count += 1
                            if no_new_items_count >= 10:  # If we haven't seen new items in 5 attempts
                                print("No new items found in last 5 attempts, proceeding with current results")
                                break
                
                time.sleep(5)  # Increased from 2 to 5 seconds
                attempt += 1
                print(f"Waiting for results... attempt {attempt}/{max_attempts}")

            if not items:
                print("No results found after maximum attempts")
                return

            print(f"Final count: {len(items)} items from API")
            new_posts_count = 0
            skipped_posts = 0
            error_posts = 0
            processed_posts = 0

            # Shuffle items to get random selection each time
            random.shuffle(items)

            # Keep trying until we either add enough posts or run out of posts to check
            while new_posts_count < db_limit and processed_posts < len(items):
                item = items[processed_posts]
                processed_posts += 1

                try:
                    # Check if post already exists using just the account_id
                    self.cur.execute('''
                        SELECT id FROM reddit_posts WHERE account_id = ?
                    ''', (item.get('userId'),))
                    if self.cur.fetchone():
                        print(f"Skipping duplicate post from user {item.get('username')} (ID: {item.get('userId')})")
                        skipped_posts += 1
                        continue

                    # First insert or get the user
                    self.cur.execute('''
                        INSERT OR IGNORE INTO reddit_users 
                        (username, user_id, karma, account_created, is_moderator, is_verified)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        item.get('username'),
                        item.get('userId'),
                        0,  # Default karma
                        self.convert_timestamp(item.get('createdAt')),
                        False,  # Default is_moderator
                        False  # Default is_verified
                    ))

                    # Get the user's integer ID
                    self.cur.execute('''
                        SELECT id FROM reddit_users WHERE user_id = ?
                    ''', (item.get('userId'),))
                    user_row = self.cur.fetchone()
                    if not user_row:
                        print(f"Failed to get user ID for {item.get('username')}")
                        error_posts += 1
                        continue
                    user_id = user_row[0]

                    text_content = f"{item.get('title', '')}\n{item.get('body', '')}"

                    # Insert the post with the integer user_id
                    self.cur.execute('''
                        INSERT INTO reddit_posts 
                        (user_id, account_id, account_name, post_date, text_content, is_reply, subreddit, upvotes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        item.get('userId'),
                        item.get('username'),
                        self.convert_timestamp(item.get('createdAt')),
                        text_content.strip(),
                        False,
                        item.get('parsedCommunityName'),
                        item.get('upVotes', 0)
                    ))
                    new_posts_count += 1
                    print(f"Added new post from {item.get('username')}")

                except Exception as e:
                    print(f"Error processing item: {e}")
                    print(f"Problematic item: {json.dumps(item, indent=2)}")
                    error_posts += 1
                    continue

            self.conn.commit()
            print(f"\nScraping Summary:")
            print(f"Total items from API: {len(items)}")
            print(f"Processed posts: {processed_posts}")
            print(f"New posts added: {new_posts_count}")
            print(f"Skipped (duplicate) posts: {skipped_posts}")
            print(f"Error posts: {error_posts}")

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
        scraper.scrape_posts(api_limit=150, db_limit=25)
    finally:
        scraper.close() 