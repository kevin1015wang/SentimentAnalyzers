import sqlite3
import os
from pathlib import Path
import json
from datetime import datetime

def analyze_account_age_sentiment():
    # Get the absolute path to the database
    db_path = Path(__file__).parent.parent / 'data' / 'project.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Define account age ranges in months
        age_ranges = [
            (0, 3),     
            (3, 6),      
            (6, 12),   
            (12, 24),    
            (24, 36),    
            (36, 60),
            (60, 84),   
            (84, 120),   
            (120, None)  
        ]
        
        results = []
        
        for min_age, max_age in age_ranges:
            # Build the query with appropriate age range condition
            if max_age is None:
                age_condition = "(strftime('%m', 'now') + 12 * strftime('%Y', 'now')) - (strftime('%m', account_created) + 12 * strftime('%Y', account_created)) >= ?"
                params = (min_age,)
            else:
                age_condition = "(strftime('%m', 'now') + 12 * strftime('%Y', 'now')) - (strftime('%m', account_created) + 12 * strftime('%Y', account_created)) >= ? AND (strftime('%m', 'now') + 12 * strftime('%Y', 'now')) - (strftime('%m', account_created) + 12 * strftime('%Y', account_created)) < ?"
                params = (min_age, max_age)
            
            # Join users and posts tables, group by account age range
            query = f"""
                SELECT 
                    COUNT(DISTINCT ru.id) as user_count,
                    COUNT(rp.id) as post_count,
                    AVG(rp.trump_sentiment) as avg_sentiment
                FROM reddit_users ru
                JOIN reddit_posts rp ON ru.user_id = rp.account_id
                WHERE {age_condition}
                AND rp.trump_sentiment IS NOT NULL
            """
            
            cur.execute(query, params)
            user_count, post_count, avg_sentiment = cur.fetchone()
            
            # Format the range label
            if max_age is None:
                range_label = f"{min_age}+ months"
            else:
                range_label = f"{min_age}-{max_age} months"
            
            if user_count > 0:  # Only include ranges with data
                results.append({
                    "account_age_range": range_label,
                    "avg_sentiment": round(avg_sentiment, 2) if avg_sentiment else None
                })
        
        # Save results to JSON file
        output_path = Path(__file__).parent.parent / 'data' / 'account_age_sentiment.json'
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Analysis complete. Results saved to {output_path}")
        print("\nAccount Age Analysis (in months):")
        for result in results:
            print(f"\nAccount Age Range: {result['account_age_range']}")
            print(f"Average Sentiment: {result['avg_sentiment']}")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    analyze_account_age_sentiment() 