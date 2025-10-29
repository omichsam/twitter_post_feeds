# Twitter Tweets Manager

A Python tool to fetch, store, and manage X/Twitter tweets with automatic updates and duplicate prevention.


##  Quick Start

### 1. Install Dependencies
To get started, first install the required dependencies:
```bash
pip install requests pandas tabulate schedule python-dotenv
```

# 2. Create .env File

Create a .env file in the project directory with the following contents:

``` 
BEARER_TOKEN=your_bearer_token_here
DEFAULT_USERNAME=x_username
REFRESH_INTERVAL=60
FETCH_COUNT=100
DB_NAME=tweets.db  
```


### 3. Get API Token

i. Visit the X Developer Portal
ii. Create an app and generate a Bearer Token.
iii. Add the token to your .env file.


### 4. Run Application

Once your environment is set up, run the application:

``` python tweet_manager.py  ```


## Features

- Database Storage: SQLite with automatic table creation.

- Duplicate Prevention: Smart ID tracking to avoid duplicate tweets.

- Auto Refresh: Scheduled updates to keep your data fresh.

- CSV Export: Backup and analysis of your tweets in CSV format.

- Env Configuration: Secure management of sensitive tokens.

- Programmatic API: Integrate into your own projects with ease.

## Usage
#### Interactive Menu

When you run the program, you’ll be presented with an interactive menu to manage your tweets:

```
1. View tweets for a user
2. Refresh tweets for a user
3. Start auto-refresh daemon
4. Show configuration
5. Use default user from .env
6. Exit
```

### Configuration

| Setting              | Description                 | Default   |
| -------------------- | --------------------------- | --------- |
| **BEARER_TOKEN**     | API authentication          | Required  |
| **DEFAULT_USERNAME** | Default user to track       | x_username |
| **REFRESH_INTERVAL** | Auto-update frequency (min) | 60        |
| **FETCH_COUNT**      | Tweets per request          | 100       |
| **DB_NAME**          | Database file               | db_db_db.db |


## Output

Example of stored tweets for a user:

#### STORED TWEETS FOR @user (showing 5 most recent)
| Date                | Tweet            | Likes  | Retweets  | Replies  |
|---------------------|------------------|--------|-----------|----------|
| 2024-01-15 10:30:00 | Tweet text here...| 15000  | 2500      | 1200     |


## Security

- Add .env to .gitignore to ensure sensitive data is not committed to version control.

- Never commit bearer tokens to repositories or share them publicly.

- Token masking is implemented to hide tokens in the configuration display.

## Troubleshooting

- <b>401 Error:</b> Check your Bearer Token. Ensure it's valid and has the correct permissions.

- <b>429 Error:</b> Rate limit exceeded. Increase the REFRESH_INTERVAL to avoid hitting the rate limits.

- <b>No tweets returned:</b> Verify the username and check if the account’s privacy settings allow fetching data.



#### Start the Flask API server
```
python twitter_api.py
```
####  Start the Twitter Fetcher (auto-fetch twice daily)
```
python twitter_fetcher.py</i>
```

### Method 2: Using a Bash Script (Linux/Mac)
Create a file called start_services.sh:

<i> bash  code </i>

```
#!/bin/bash
echo "Starting Twitter Services..."
gnome-terminal -- python3 twitter_api.py
sleep 3
gnome-terminal -- python3 twitter_fetcher.py
echo "Both services started!  ```