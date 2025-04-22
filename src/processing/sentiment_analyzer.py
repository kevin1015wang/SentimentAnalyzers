# src/processing/sentiment_analyzer.py
import sqlite3
from textblob import TextBlob
import os
from dotenv import load_dotenv

class SentimentAnalyzer:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'project.db'))
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cur = self.conn.cursor()

    def calculate_sentiment(self, text):
        """
        Calculate sentiment score from 0-100 using TextBlob
        0 = most negative, 100 = most positive
        """
        if not text:
            return 50  # Neutral if no text
        
        # Get sentiment polarity (-1 to 1)
        sentiment = TextBlob(text).sentiment.polarity
        
        # Convert to 0-100 scale
        # -1 to 1 -> 0 to 100
        score = int((sentiment + 1) * 50)
        
        # Ensure score is within bounds
        return max(0, min(100, score))

    def analyze_reddit_posts(self):
        """Analyze sentiment of Reddit posts and update the database"""
        print("\nAnalyzing Reddit posts...")
        
        # Get all posts that haven't been analyzed yet
        self.cur.execute('''
            SELECT id, text_content 
            FROM reddit_posts 
            WHERE trump_sentiment IS NULL
        ''')
        
        posts = self.cur.fetchall()
        print(f"Found {len(posts)} Reddit posts to analyze")
        
        for post_id, text in posts:
            try:
                sentiment_score = self.calculate_sentiment(text)
                
                # Update the post with sentiment score
                self.cur.execute('''
                    UPDATE reddit_posts 
                    SET trump_sentiment = ? 
                    WHERE id = ?
                ''', (sentiment_score, post_id))
                
            except Exception as e:
                print(f"Error analyzing Reddit post {post_id}: {e}")
                continue
        
        self.conn.commit()
        print(f"Updated {len(posts)} Reddit posts with sentiment scores")

    def analyze_instagram_posts(self):
        """Analyze sentiment of Instagram posts and update the database"""
        print("\nAnalyzing Instagram posts...")
        
        # Get all posts that haven't been analyzed yet
        self.cur.execute('''
            SELECT id, caption 
            FROM instagram_posts 
            WHERE trump_sentiment IS NULL
        ''')
        
        posts = self.cur.fetchall()
        print(f"Found {len(posts)} Instagram posts to analyze")
        
        for post_id, caption in posts:
            try:
                sentiment_score = self.calculate_sentiment(caption)
                
                # Update the post with sentiment score
                self.cur.execute('''
                    UPDATE instagram_posts 
                    SET trump_sentiment = ? 
                    WHERE id = ?
                ''', (sentiment_score, post_id))
                
            except Exception as e:
                print(f"Error analyzing Instagram post {post_id}: {e}")
                continue
        
        self.conn.commit()
        print(f"Updated {len(posts)} Instagram posts with sentiment scores")

    def close(self):
        """Close database connection"""
        self.conn.close()

def main():
    analyzer = SentimentAnalyzer()
    try:
        analyzer.analyze_reddit_posts()
        analyzer.analyze_instagram_posts()
    finally:
        analyzer.close()

if __name__ == "__main__":
    main() 