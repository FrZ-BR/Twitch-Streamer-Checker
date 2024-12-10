import os
import time
import requests
import logging
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Disable TensorFlow Lite logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('twitch_script_log.log'),
                        logging.StreamHandler()
                    ])

# Load config
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Load or initialize watch progress
progress_file = 'watch_progress.json'
if os.path.exists(progress_file):
    with open(progress_file, 'r') as pf:
        watch_progress = json.load(pf)
else:
    watch_progress = {group["reward"]: 0 for group in config["streamer_groups"]}

# Webhook URL and message prefix
webhook_url = config.get("webhook_url")
message_prefix = config.get("message_prefix", "")

# Save progress
def save_watch_progress():
    with open(progress_file, 'w') as pf:
        json.dump(watch_progress, pf)

# Function to send messages to the webhook
def send_webhook_message(message):
    if not webhook_url:
        logging.warning("Webhook URL is not configured. Skipping webhook message.")
        return
    try:
        full_message = f"{message_prefix} {message}".strip()
        response = requests.post(webhook_url, json={"content": full_message})
        if response.status_code == 204:
            logging.info("Webhook message sent successfully.")
        else:
            logging.error(f"Failed to send webhook message. HTTP {response.status_code}: {response.text}")
    except Exception as e:
        logging.error(f"Error sending webhook message: {e}")

# Twitch API credentials
client_id = config["twitch_tokens"]["client_id"]
client_secret = config["twitch_tokens"]["client_secret"]

# Paths and browser settings
chrome_driver_path = config["chrome_driver_path"]
profile_path = config["profile_path"]
game_name = config["game_name"]

# Get Twitch access token
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

# Check if a streamer is online and playing the specified game
def is_streamer_online_and_playing(access_token, client_id, streamer_name, game_name):
    logging.info(f'Checking if {streamer_name} is online and playing {game_name}...')
    url = f'https://api.twitch.tv/helix/streams'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Client-Id': client_id
    }
    params = {'user_login': streamer_name}
    response = requests.get(url, headers=headers, params=params)
    data = response.json().get('data', [])
    
    if data and data[0]['type'] == 'live':
        current_game = data[0].get('game_name', '').lower()
        if current_game == game_name.lower():
            logging.info(f'{streamer_name} is online and playing {game_name}.')
            return True
        else:
            logging.info(f'{streamer_name} is online but playing {current_game} instead of {game_name}.')
    else:
        logging.info(f'{streamer_name} is not online.')
    return False

# Chrome options
chrome_options = Options()
chrome_options.add_argument(f"user-data-dir={profile_path}")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--remote-debugging-port=9222")

# Start ChromeDriver service
service = Service(chrome_driver_path)

# Get access token
access_token = get_access_token(client_id, client_secret)

# Loop through reward groups until all are completed
while True:
    # Recalcular recompensas incompletas no início de cada iteração
    incomplete_groups = [
        group for group in config["streamer_groups"]
        if watch_progress[group["reward"]] < group["total_watch_time"]
    ]
    
    total_remaining = len(incomplete_groups)  # Recalcular o total de recompensas restantes

    if not incomplete_groups:
        logging.info('All rewards have been completed. Exiting...')
        send_webhook_message("✅ All rewards have been completed.")
        break

    for group in incomplete_groups:
        reward = group["reward"]
        total_watch_time = group["total_watch_time"]
        time_watched = watch_progress[reward]
        
        if time_watched >= total_watch_time:
            logging.info(f'Reward "{reward}" is already completed. Skipping...')
            continue

        for streamer in group["streamers"]:
            streamer_name = streamer["name"]

            try:
                driver = webdriver.Chrome(service=service, options=chrome_options)

                if is_streamer_online_and_playing(access_token, client_id, streamer_name, game_name):
                    url = f'https://www.twitch.tv/{streamer_name}'
                    remaining = total_watch_time - time_watched
                    mins, secs = divmod(remaining, 60)
                    send_webhook_message(f"🎥 Starting to watch {streamer_name} for reward '{reward}'. "
                                         f"Time remaining: {mins} minutes and {secs} seconds. "
                                         f"Remaining rewards: {total_remaining}.")
                    logging.info(f'Opening URL: {url}')
                    driver.get(url)

                    start_time = time.time()
                    while time_watched < total_watch_time:
                        time.sleep(1)
                        time_watched += 1
                        watch_progress[reward] = min(time_watched, total_watch_time)
                        save_watch_progress()

                        remaining = total_watch_time - time_watched
                        mins, secs = divmod(remaining, 60)
                        os.system(f'title Watching {streamer_name} for reward "{reward}" - Remaining: {mins:02d}:{secs:02d}')

                        if remaining % 300 == 0:  # Every 5 minutes
                            send_webhook_message(f"⏳ {streamer_name} - Reward '{reward}': {mins} minutes and {secs} seconds remaining. "
                                                 f"Remaining rewards: {total_remaining}.")

                    # Atualizar total_remaining após a conclusão da recompensa
                    total_remaining -= 1
                    send_webhook_message(f"✅ Completed reward '{reward}' by watching {streamer_name}. Remaining rewards: {total_remaining}.")
                    logging.info(f'Time completed for reward "{reward}". Closing browser...')
                    driver.quit()
                    break

                else:
                    logging.info(f'{streamer_name} is not online or not playing {game_name}. Skipping...')
                    send_webhook_message(f"⚠️ {streamer_name} is not online or not playing {game_name}. Trying another streamer...")
                    driver.quit()

            except Exception as e:
                logging.error(f'Error with {streamer_name}: {e}')
                send_webhook_message(f"❌ Error while processing {streamer_name}: {e}")
                driver.quit()
