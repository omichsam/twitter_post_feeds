from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes

DB_NAME = os.getenv('DB_NAME', 'twitter_posts.db')
DEFAULT_USERNAME = os.getenv('DEFAULT_USERNAME', 'Whitebox_Ke')

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/posts', methods=['GET'])
def get_default_user_posts():
    """Get posts for the default user in descending order"""
    try:
        # Get limit parameter with validation
        limit = request.args.get('limit', default=10, type=int)
        
        if limit < 1:
            return jsonify({
                'success': False, 
                'error': 'Limit must be at least 1'
            }), 400
        
        if limit > 1000:
            return jsonify({
                'success': False, 
                'error': 'Limit cannot exceed 1000'
            }), 400

        conn = get_db_connection()
        
        # Get posts for default user in descending order (newest first)
        posts = conn.execute('''
            SELECT * FROM posts 
            WHERE username = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (DEFAULT_USERNAME, limit)).fetchall()
        
        # Get total count for default user
        total_count = conn.execute(
            'SELECT COUNT(*) FROM posts WHERE username = ?', (DEFAULT_USERNAME,)
        ).fetchone()[0]
        
        conn.close()
        
        posts_list = [dict(post) for post in posts]
        
        return jsonify({
            'success': True,
            'username': DEFAULT_USERNAME,
            'posts': posts_list,
            'count': len(posts_list),
            'total_count': total_count,
            'limit': limit
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.execute('SELECT 1')
        
        # Check if we have data for default user
        user_count = conn.execute(
            'SELECT COUNT(*) FROM posts WHERE username = ?', 
            (DEFAULT_USERNAME,)
        ).fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'database': DB_NAME,
            'default_user': DEFAULT_USERNAME,
            'user_posts_count': user_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print(f"🚀 Starting API server for default user: @{DEFAULT_USERNAME}")
    print("📡 Server running on http://localhost:8010")
    print("🔗 CORS enabled for all origins")
    app.run(debug=True, host='0.0.0.0', port=8010)