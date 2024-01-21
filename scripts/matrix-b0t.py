from nio import AsyncClient, RoomMessageText, MatrixRoom, LoginResponse
import requests
import configparser
import os
import asyncio

# Read the configuration file
config = configparser.ConfigParser()
config_path = os.getenv('CONFIG_PATH', '/config/config.ini')  # Use the environment variable CONFIG_PATH. If it doesn't exist, default to 'config.ini'.
if not os.path.exists(config_path):
    raise Exception(f"Konfigurationsdatei {config_path} existiert nicht")
    exit()
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

async def on_invite(room_id, state):
    print(f"Invited to room: {room_id}")
    await client.join(room_id)
    print(f"Joined room: {room_id}")
    # Write room ID to ID database file
    with open(joined_rooms_file, 'a') as file:
        file.write(room_id + '\n')

# Function to trigger a webhook
async def trigger_webhook(url):
    try:
        response = await requests.post(url)
        response.raise_for_status()  # Check if the request was successful
    except requests.exceptions.RequestException as e:
        print(f"Error triggering webhook: {e}")

# Function to respond to messages
async def on_message(room: MatrixRoom, event: RoomMessageText):
    if event.body.startswith(prefix):
        command = event.body[len(prefix):]  # Remove the prefix
        if event.sender in user_commands:
            if command in user_commands[event.sender]:
                await trigger_webhook(commands[command])
                await client.room_send(
                    room.room_id,
                    message_type="m.room.message",
                    content={
                        "msgtype": "m.text",
                        "body": "command webhook triggered!"
                    }
                )

# Check the configuration at program startup
check_config(config)

# Initialize Matrix client
client = AsyncClient(matrix_server_url, matrix_username)

# Login
if matrix_token:
    client.access_token = matrix_token
    client.user_id = matrix_username
else:
    response = asyncio.run(client.login(matrix_password))
    if isinstance(response, LoginResponse):
        print(f"Logged in as {response.user_id}")
    else:
        print(f"Failed to log in: {response}")

# Add the invite listener
client.add_invite_listener(on_invite)

# Join room and respond to messages
for room_id in joined_rooms:
    try:
        asyncio.run(client.join(room_id))
        client.add_event_callback(on_message, RoomMessageText)
    except Exception as e:
        print(f"Error joining room: {e}")
        exit()

# Start the bot
try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.sync_forever(timeout=30000))  # timeout in milliseconds
except Exception as e:
    print(f"Error starting the bot: {e}")
    exit()
