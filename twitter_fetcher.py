import requests
import sqlite3
import schedule
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BEARER_TOKEN = os.getenv('BEARER_TOKEN')
DEFAULT_USERNAME = os.getenv('DEFAULT_USERNAME', 'Whitebox_Ke')
DB_NAME = os.getenv('DB_NAME', 'twitter_posts.db')
SCHEDULE_HOURS = int(os.getenv('SCHEDULE_HOURS', 8))
FETCH_COUNT = int(os.getenv('FETCH_COUNT', 100))

def init_database():
    """Initialize database with posts table"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            like_count INTEGER DEFAULT 0,
            retweet_count INTEGER DEFAULT 0,
            reply_count INTEGER DEFAULT 0,
            url TEXT NOT NULL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_posts_username_created 
        ON posts(username, created_at DESC)
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_NAME}")

def get_user_id(username):
    """Get user ID from username"""
    url = f"https://api.x.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()["data"]["id"]
        else:
            print(f"❌ Error getting user ID: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception getting user ID: {e}")
        return None

def fetch_default_user_posts():
    """Fetch posts from the default user specified in .env"""
    username = DEFAULT_USERNAME
    print(f"🔄 Fetching posts for default user: @{username}...")
    
    user_id = get_user_id(username)
    if not user_id:
        print(f"❌ Could not find user @{username}")
        return
    
    url = f"https://api.x.com/2/users/{user_id}/tweets"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    params = {
        "max_results": min(FETCH_COUNT, 100),
        "tweet.fields": "created_at,public_metrics",
        "exclude": "retweets"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return
        
        tweets = response.json().get("data", [])
        print(f"📥 Fetched {len(tweets)} posts for @{username}")
        
        if not tweets:
            print(f"ℹ️ No posts found for @{username}")
            return
        
        # Store in database
        store_posts(username, tweets)
        
    except Exception as e:
        print(f"❌ Error fetching posts: {e}")

def store_posts(username, tweets_data):
    """Store posts in database without duplicates"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    new_posts = 0
    duplicate_posts = 0
    
    for tweet in tweets_data:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO posts 
                (id, username, text, created_at, like_count, retweet_count, reply_count, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tweet["id"],
                username,
                tweet["text"],
                tweet["created_at"],
                tweet["public_metrics"]["like_count"],
                tweet["public_metrics"]["retweet_count"],
                tweet["public_metrics"]["reply_count"],
                f"https://x.com/i/web/status/{tweet['id']}"
            ))
            
            if cursor.rowcount > 0:
                new_posts += 1
            else:
                duplicate_posts += 1
                
        except Exception as e:
            print(f"❌ Error storing post {tweet['id']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"💾 Stored {new_posts} new posts, {duplicate_posts} duplicates for @{username}")

def schedule_fetcher():
    """Schedule automatic fetching twice daily for default user only"""
    print(f"⏰ Scheduling automatic fetches for @{DEFAULT_USERNAME} twice daily...")
    
    # Schedule at 8 AM and 8 PM
    schedule.every().day.at("06:00").do(fetch_default_user_posts)
    schedule.every().day.at("12:00").do(fetch_default_user_posts)
    schedule.every().day.at("19:00").do(fetch_default_user_posts)
    
    print("✅ Scheduled: 6:00 AM , 12:00 PM and 7:00 PM daily")
    print(f"🎯 Only fetching from: @{DEFAULT_USERNAME}")
    
    # Do an initial fetch immediately
    print("🚀 Performing initial fetch...")
    fetch_default_user_posts()
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def manual_fetch():
    """Manually fetch posts for the default user"""
    if not BEARER_TOKEN:
        print("❌ BEARER_TOKEN not found in .env file")
        return
    
    if not DEFAULT_USERNAME:
        print("❌ DEFAULT_USERNAME not found in .env file")
        return
        
    init_database()
    fetch_default_user_posts()

if __name__ == "__main__":
    import sys
    
    # Always use the default user from .env
    print(f"🎯 Using default user from .env: @{DEFAULT_USERNAME}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        # Manual fetch: python twitter_fetcher.py manual
        manual_fetch()
    else:
        # Start scheduler for default user only
        init_database()
        print("🚀 Starting Twitter Fetcher Scheduler for default user...")
        print("Press Ctrl+C to stop")
        try:
            schedule_fetcher()
        except KeyboardInterrupt:
            print("\n⏹️ Scheduler stopped")