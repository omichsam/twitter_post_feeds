from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes

DB_NAME = os.getenv('DB_NAME', 'twitter_posts.db')
DEFAULT_USERNAME = os.getenv('DEFAULT_USERNAME', 'Whitebox_Ke')
API_PORT = int(os.getenv('API_PORT', 8010))

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/posts', methods=['GET'])
def get_all_posts():
    """Get all posts from all users in descending order"""
    try:
        # Get query parameters with validation
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)
        username = request.args.get('username', default=None, type=str)
        
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
        
        if offset < 0:
            return jsonify({
                'success': False, 
                'error': 'Offset cannot be negative'
            }), 400

        conn = get_db_connection()
        
        # Build query based on parameters
        query = 'SELECT * FROM posts'
        params = []
        
        if username:
            query += ' WHERE username = ?'
            params.append(username)
        
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        posts = conn.execute(query, params).fetchall()
        
        # Get total count
        count_query = 'SELECT COUNT(*) FROM posts'
        count_params = []
        
        if username:
            count_query += ' WHERE username = ?'
            count_params.append(username)
        
        total_count = conn.execute(count_query, count_params).fetchone()[0]
        
        conn.close()
        
        posts_list = [dict(post) for post in posts]
        
        return jsonify({
            'success': True,
            'posts': posts_list,
            'count': len(posts_list),
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'username_filter': username if username else 'all'
        })
        
    except Exception as e:
        app.logger.error(f"Error in /api/posts: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/api/posts/default', methods=['GET'])
def get_default_user_posts():
    """Get posts for the default user in descending order"""
    try:
        # Get limit parameter with validation
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
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
        
        if offset < 0:
            return jsonify({
                'success': False, 
                'error': 'Offset cannot be negative'
            }), 400

        conn = get_db_connection()
        
        # Get posts for default user in descending order (newest first)
        posts = conn.execute('''
            SELECT * FROM posts 
            WHERE username = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', (DEFAULT_USERNAME, limit, offset)).fetchall()
        
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
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        app.logger.error(f"Error in /api/posts/default: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/api/posts/latest', methods=['GET'])
def get_latest_posts():
    """Get latest posts from the last N hours"""
    try:
        hours = request.args.get('hours', default=24, type=int)
        limit = request.args.get('limit', default=50, type=int)
        username = request.args.get('username', default=None, type=str)
        
        if hours < 1:
            return jsonify({
                'success': False, 
                'error': 'Hours must be at least 1'
            }), 400
        
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

        # Calculate datetime for X hours ago
        from datetime import datetime, timedelta
        hours_ago = datetime.utcnow() - timedelta(hours=hours)
        hours_ago_str = hours_ago.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        conn = get_db_connection()
        
        # Build query
        query = '''
            SELECT * FROM posts 
            WHERE created_at >= ?
        '''
        params = [hours_ago_str]
        
        if username:
            query += ' AND username = ?'
            params.append(username)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        posts = conn.execute(query, params).fetchall()
        
        # Get count for the period
        count_query = 'SELECT COUNT(*) FROM posts WHERE created_at >= ?'
        count_params = [hours_ago_str]
        
        if username:
            count_query += ' AND username = ?'
            count_params.append(username)
        
        period_count = conn.execute(count_query, count_params).fetchone()[0]
        
        conn.close()
        
        posts_list = [dict(post) for post in posts]
        
        return jsonify({
            'success': True,
            'posts': posts_list,
            'count': len(posts_list),
            'period_count': period_count,
            'hours': hours,
            'limit': limit,
            'username_filter': username if username else 'all',
            'since': hours_ago_str
        })
        
    except Exception as e:
        app.logger.error(f"Error in /api/posts/latest: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/api/posts/<string:post_id>', methods=['GET'])
def get_single_post(post_id):
    """Get a single post by ID"""
    try:
        conn = get_db_connection()
        
        post = conn.execute(
            'SELECT * FROM posts WHERE id = ?', (post_id,)
        ).fetchone()
        
        conn.close()
        
        if post is None:
            return jsonify({
                'success': False,
                'error': 'Post not found'
            }), 404
        
        return jsonify({
            'success': True,
            'post': dict(post)
        })
        
    except Exception as e:
        app.logger.error(f"Error in /api/posts/{post_id}: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/api/users', methods=['GET'])
def get_all_users():
    """Get list of all tracked users with stats"""
    try:
        conn = get_db_connection()
        
        users = conn.execute('''
            SELECT 
                username,
                COUNT(*) as post_count,
                MAX(created_at) as latest_post,
                MIN(created_at) as earliest_post,
                SUM(like_count) as total_likes,
                SUM(retweet_count) as total_retweets,
                SUM(reply_count) as total_replies
            FROM posts 
            GROUP BY username 
            ORDER BY post_count DESC
        ''').fetchall()
        
        conn.close()
        
        users_list = [dict(user) for user in users]
        
        return jsonify({
            'success': True,
            'users': users_list,
            'count': len(users_list)
        })
        
    except Exception as e:
        app.logger.error(f"Error in /api/users: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get overall statistics"""
    try:
        conn = get_db_connection()
        
        # Overall stats
        overall = conn.execute('''
            SELECT 
                COUNT(*) as total_posts,
                COUNT(DISTINCT username) as total_users,
                MAX(created_at) as latest_post,
                MIN(created_at) as earliest_post,
                SUM(like_count) as total_likes,
                SUM(retweet_count) as total_retweets,
                SUM(reply_count) as total_replies,
                SUM(impression_count) as total_impressions
            FROM posts
        ''').fetchone()
        
        # Default user stats
        default_user = conn.execute('''
            SELECT 
                COUNT(*) as post_count,
                MAX(created_at) as latest_post,
                SUM(like_count) as total_likes,
                SUM(retweet_count) as total_retweets
            FROM posts 
            WHERE username = ?
        ''', (DEFAULT_USERNAME,)).fetchone()
        
        # Recent activity (last 7 days)
        week_ago = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        recent = conn.execute('''
            SELECT 
                COUNT(*) as posts_last_7_days,
                SUM(like_count) as likes_last_7_days
            FROM posts 
            WHERE created_at >= ?
        ''', (week_ago,)).fetchone()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'statistics': {
                'overall': dict(overall),
                'default_user': {
                    'username': DEFAULT_USERNAME,
                    **dict(default_user)
                } if default_user['post_count'] > 0 else {
                    'username': DEFAULT_USERNAME,
                    'post_count': 0,
                    'message': 'No posts found for default user'
                },
                'recent_activity': dict(recent)
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error in /api/stats: {str(e)}")
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
        
        # Get table info
        table_info = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        
        tables = [row[0] for row in table_info]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'database': DB_NAME,
            'tables': tables,
            'default_user': DEFAULT_USERNAME,
            'default_user_posts_count': user_count,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/', methods=['GET'])
def index():
    """API Documentation"""
    endpoints = {
        'endpoints': {
            '/api/posts': {
                'method': 'GET',
                'description': 'Get all posts with pagination',
                'parameters': {
                    'limit': 'Number of posts to return (default: 50, max: 1000)',
                    'offset': 'Pagination offset (default: 0)',
                    'username': 'Filter by username (optional)'
                }
            },
            '/api/posts/default': {
                'method': 'GET',
                'description': f'Get posts for default user (@{DEFAULT_USERNAME})',
                'parameters': {
                    'limit': 'Number of posts to return (default: 50, max: 1000)',
                    'offset': 'Pagination offset (default: 0)'
                }
            },
            '/api/posts/latest': {
                'method': 'GET',
                'description': 'Get latest posts from the last N hours',
                'parameters': {
                    'hours': 'Number of hours to look back (default: 24)',
                    'limit': 'Number of posts to return (default: 50, max: 1000)',
                    'username': 'Filter by username (optional)'
                }
            },
            '/api/posts/<id>': {
                'method': 'GET',
                'description': 'Get a single post by ID'
            },
            '/api/users': {
                'method': 'GET',
                'description': 'Get list of all tracked users with statistics'
            },
            '/api/stats': {
                'method': 'GET',
                'description': 'Get overall statistics'
            },
            '/health': {
                'method': 'GET',
                'description': 'Health check endpoint'
            }
        },
        'default_user': DEFAULT_USERNAME,
        'database': DB_NAME
    }
    
    return jsonify(endpoints)

if __name__ == '__main__':
    print(f"🚀 Starting Twitter Posts API Server")
    print(f"📡 Server running on http://localhost:{API_PORT}")
    print(f"🎯 Default user: @{DEFAULT_USERNAME}")
    print(f"🗄️  Database: {DB_NAME}")
    print("🔗 CORS enabled for all origins")
    print("\n📚 Available endpoints:")
    print("  GET /              - API documentation")
    print("  GET /api/posts     - Get all posts (with pagination)")
    print(f"  GET /api/posts/default - Get posts for @{DEFAULT_USERNAME}")
    print("  GET /api/posts/latest - Get latest posts from last N hours")
    print("  GET /api/posts/<id> - Get single post by ID")
    print("  GET /api/users     - Get all tracked users")
    print("  GET /api/stats     - Get statistics")
    print("  GET /health        - Health check")
    
    app.run(debug=True, host='0.0.0.0', port=API_PORT)