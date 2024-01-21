from matrix_client.client import MatrixClient
import requests
import configparser
import os

# Read the configuration file
config = configparser.ConfigParser()
config_path = os.getenv('CONFIG_PATH', '/config/config.ini')  # Use the environment variable CONFIG_PATH. If it doesn't exist, default to 'config.ini'.
config_base_path = os.path.dirname(config_path)
joined_rooms_file = os.path.join(config_base_path, 'joined-rooms.txt')

config.read(config_path)

# Dictionary of users and their allowed commands
user_commands = {user: commands.split(',') for user, commands in config['Users'].items()}

# Dictionary of commands and webhook URLs
commands = {command: url for command, url in config['Webhooks'].items()}

# Matrix server URL
matrix_server_url = config['Matrix']['server_url']

# Matrix username and password
matrix_username = config['Matrix']['username']
matrix_password = config['Matrix']['password']
matrix_token = config['Matrix']['token']

# Matrix room ID
matrix_room_id = config['Matrix']['room_id']

# command prefix
prefix = config['Matrix'].get('command_prefix', '!b0t')

# Required configuration keys
REQUIRED_CONFIG = {
    'Matrix': ['server_url', 'room_id'],
    'Users': [],
    'Webhooks': []
}

# Open the file in read and write mode
with open(joined_rooms_file, 'r+') as file:
    # Read each line in the file
    joined_rooms = [line.strip() for line in file]


def check_config(config):
    for section, keys in REQUIRED_CONFIG.items():
        if section not in config:
            raise Exception(f"Missing section {section} in config file")
        for key in keys:
            if key not in config[section]:
                raise Exception(f"Missing key {key} in section {section} in config file")
    if 'Matrix' in config:
        matrix_section = config['Matrix']
        if 'token' not in matrix_section and ('username' not in matrix_section or 'password' not in matrix_section):
            raise Exception("Either 'token' or 'username' and 'password' are required in the 'Matrix' section of the config file")

def on_invite(room_id, state):
    print(f"Invited to room: {room_id}")
    room = client.join_room(room_id)
    print(f"Joined room: {room_id}")
    # Write room ID to ID database file
    with open(joined_rooms_file, 'a') as file:
        file.write(room_id + '\n')


# Function to trigger a webhook
def trigger_webhook(url):
    try:
        response = requests.post(url)
        response.raise_for_status()  # Check if the request was successful
    except requests.exceptions.RequestException as e:
        print(f"Error triggering webhook: {e}")

# Function to respond to messages
def on_message(room, event):
    if event['content']['msgtype'] == "m.text":
        command = event['content']['body']
        prefix_length = len(prefix)
        if command.startswith(prefix):
            command = command[prefix_length:]  # Remove the prefix
            if event['sender'] in user_commands:
                if command in user_commands[event['sender']]:
                    trigger_webhook(commands[command])

# Check the configuration at program startup
check_config(config)

# Initialize Matrix client
try:
    client = MatrixClient(matrix_server_url)
except Exception as e:
    print(f"Error initializing Matrix client: {e}")
    exit()

# Login
try:
    if matrix_token:
        client.login(token=matrix_token)
    else:
        client.login(username=matrix_username, password=matrix_password)
except Exception as e:
    print(f"Error logging in: {e}")
    exit()

# Add the invite listener
client.add_invite_listener(on_invite)

# Join room and respond to messages
for room_id in joined_rooms:
    try:
        room = client.join_room(room_id)
        room.add_listener(on_message)
    except Exception as e:
        print(f"Error joining room: {e}")
        exit()

# Start the bot
try:
    client.start_listener_thread()
except Exception as e:
    print(f"Error starting the bot: {e}")
    exit()
