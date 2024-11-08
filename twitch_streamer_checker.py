import os
import time
import requests
import logging
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Disable INFO and WARNING logs from TensorFlow Lite
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Logging configuration to display on console and save to file
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('twitch_script_log.log'),
                        logging.StreamHandler()
                    ])

# Load configurations from the JSON file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Load or create watch progress file
progress_file = 'watch_progress.json'
if os.path.exists(progress_file):
    with open(progress_file, 'r') as pf:
        watch_progress = json.load(pf)
else:
    watch_progress = {streamer["name"]: 0 for streamer in config["streamers"]}

# Save watch progress
def save_watch_progress():
    with open(progress_file, 'w') as pf:
        json.dump(watch_progress, pf)

# Twitch API credentials
client_id = config["twitch_tokens"]["client_id"]
client_secret = config["twitch_tokens"]["client_secret"]

# Paths and browser configurations
chrome_driver_path = config["chrome_driver_path"]
profile_path = config["profile_path"]
game_name = config["game_name"]

# Get access token
def get_access_token(client_id, client_secret):
    logging.info('Obtaining access token...')
    url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, params=params)
    access_token = response.json().get('access_token')
    logging.info('Access token obtained.')
    return access_token

# Check if the streamer is online and playing a specific game
def is_streamer_online_and_playing(access_token, client_id, streamer_name, game_name):
    logging.info(f'Checking if {streamer_name} is online and playing {game_name}...')
    url = f'https://api.twitch.tv/helix/streams'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Client-Id': client_id
    }
    params = {
        'user_login': streamer_name
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json().get('data', [])
    
    if len(data) > 0 and data[0]['type'] == 'live':
        current_game = data[0].get('game_name', '').lower()
        if current_game == game_name.lower():
            logging.info(f'{streamer_name} is online and playing {game_name}.')
            return True
        else:
            logging.info(f'{streamer_name} is online but not playing {game_name} (playing {current_game} instead).')
    else:
        logging.info(f'{streamer_name} is not online.')
    
    return False

# List of streamers and times to check
streamers_with_time = config["streamers"]

# Chrome options
chrome_options = Options()
chrome_options.add_argument(f"user-data-dir={profile_path}")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--remote-debugging-port=9222")  # For remote debugging

# Start ChromeDriver service
service = Service(chrome_driver_path)

# Get access token
access_token = get_access_token(client_id, client_secret)

# Loop to check all streamers until all are completed
while True:
    # Check if all streamers have been watched for the required time
    incompletes = [streamer for streamer in streamers_with_time if watch_progress[streamer["name"]] < streamer["watch_time"]]
    if not incompletes:
        logging.info('All streamers have been watched for the required time. Finishing...')
        break

    for streamer in incompletes:
        streamer_name = streamer["name"]
        watch_time = streamer["watch_time"]

        # Check how much time has already been watched
        time_watched = watch_progress.get(streamer_name, 0)
        if time_watched >= watch_time:
            logging.info(f'Required time for {streamer_name} has already been reached. Skipping...')
            continue

        try:
            # Create a new WebDriver session for each streamer
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Check if the streamer is online and playing the specific game
            if is_streamer_online_and_playing(access_token, client_id, streamer_name, game_name):
                # Build the Twitch channel URL
                url = f'https://www.twitch.tv/{streamer_name}'
                logging.info(f'Opening URL {url}')
                
                # Open the URL
                driver.get(url)
                
                # Monitoring time counter
                start_time = time.time()
                last_check_time = time.time()  # Store the time of the last check

                while time_watched < watch_time:
                    # Calculate elapsed time, remaining time, and time to the next check
                    elapsed_time = time.time() - start_time
                    time_watched += 1
                    watch_progress[streamer_name] = time_watched
                    save_watch_progress()
                    remaining_time = watch_time - time_watched
                    time_to_next_check = 300 - int(time.time() - last_check_time)

                    if remaining_time <= 0:
                        break
                    
                    mins, secs = divmod(time_watched, 60)
                    elapsed_time_formatted = f'{mins:02d}:{secs:02d}'
                    
                    mins_rem, secs_rem = divmod(remaining_time, 60)
                    remaining_time_formatted = f'{mins_rem:02d}:{secs_rem:02d}'
                    
                    mins_check, secs_check = divmod(time_to_next_check, 60)
                    time_to_next_check_formatted = f'{mins_check:02d}:{secs_check:02d}'
                    
                    # Update CMD window title with watched time, remaining time, and time to the next check
                    os.system(f'title Watching {streamer_name} - Watched time: {elapsed_time_formatted} - Remaining time: {remaining_time_formatted} - Next check: {time_to_next_check_formatted}')
                    
                    time.sleep(1)  # Wait 1 second to continuously update the time
                    
                    # Check if the streamer is still playing the specified game every 5 minutes
                    if time_to_next_check <= 0:
                        if not is_streamer_online_and_playing(access_token, client_id, streamer_name, game_name):
                            logging.info(f'{streamer_name} changed game or went offline. Closing tab...')
                            break
                        last_check_time = time.time()  # Update the time of the last check
                
                logging.info(f'Required time for {streamer_name} is over. Closing tab...')
                driver.quit()

            else:
                logging.info(f'{streamer_name} is not playing {game_name}, skipping...')
                driver.quit()  # Ensure the browser is closed when skipping a streamer

        except Exception as e:
            logging.error(f'Error with {streamer_name}: {e}')
            driver.quit()  # Ensure the browser is closed in case of error

# Ensure all browsers are closed after the loop
logging.info('All streamers have been checked. Browser closed.')
