# Twitch Streamer Checker

This script allows you to monitor Twitch streamers, ensuring they are playing a specific game and displaying the time watched, time remaining, and time until the next check in the CMD window title.

## How to Obtain Twitch API Tokens

To use the Twitch API with your script, you need to obtain a `client_id` and a `client_secret`. These tokens are required to authenticate your requests to Twitch's API.

### Step 1: Create a Twitch Developer Account

1. Visit the [Twitch Developer Console](https://dev.twitch.tv/console).
2. Log in with your Twitch account. If you don't have a Twitch account, you'll need to create one.

### Step 2: Register Your Application

1. Once logged in, go to the [Applications](https://dev.twitch.tv/console/apps) page.
2. Click on "Register Your Application".
3. Fill in the required information:
   - **Name:** Choose a name for your application.
   - **OAuth Redirect URLs:** You can use `http://localhost` if you're testing locally or leave it empty.
   - **Category:** Select a category that fits your application (e.g., "Website Integration").
4. Click "Create".

### Step 3: Get Your Client ID and Client Secret

1. After creating your application, you'll see it listed under "Applications".
2. Click on "Manage" next to your application.
3. Here, you'll find your **Client ID**. Copy this value.
4. To obtain the **Client Secret**, click on "New Secret". This will generate a new secret. Copy and store this value securely, as you'll need it for the script.

### Step 4: Create a Chrome Profile

To ensure that the script works correctly and maintains login sessions, it's recommended to create a separate Chrome profile. This profile will be used by the script when automating the browser.

1. **Open Chrome:** Launch the Google Chrome browser.
2. **Access Profile Settings:** Click on the profile icon at the top-right corner of the Chrome window and select "Add".
3. **Create a New Profile:** Choose a name, select an icon, and click "Add". A new Chrome window will open with your new profile.
   - *RUN TO CREATE THE PROFILE:**" `C:/Program Files/Google/Chrome/Application/chrome.exe" --user-data-dir="C:/Users/YourUsername/AppData/Local/Google/Chrome/User Data/Profile X"` where `X` is the profile number
   - Access https://twitch.tv and log-in with your credetendials (THIS IS THE ONLY WAY TO BE ABLE TO LOGIN ON TWITCH. USE THE SAME PROFILE ABOVE TO USE ON THE SCRIPT)
4. **Locate Profile Path:** 
   - **Windows:** The profile path will be something like `C:/Users/YourUsername/AppData/Local/Google/Chrome/User Data/Profile X`, where `X` is the profile number (SAME AS ABOVE). 
   - **Mac/Linux:** The path will be similar but within your home directory.

### Step 4: Add the Tokens and Profile Path to the Script Configuration

1. Open the `config.json` file that the script uses.
2. Add the `client_id`, `client_secret`, and `profile_path` values under the corresponding sections:

   ```json
   {
       "twitch_tokens": {
           "client_id": "your_client_id_here",
           "client_secret": "your_client_secret_here"
       },
       "streamers": [
           {"name": "YAKOV", "watch_time": 7200},
           {"name": "ZChum", "watch_time": 7200}
       ],
       "chrome_driver_path": "C:/Path/To/Your/chromedriver.exe",
       "profile_path": "C:/Users/YourUsername/AppData/Local/Google/Chrome/User Data/Profile 1",
       "game_name": "Rust"
   }


### Step 6: Log in to your Twitch account in the Chrome profile that is created the first time you run the script.
