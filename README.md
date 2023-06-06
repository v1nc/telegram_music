# Telegram Music
_Search for music in your telegram channels and download it, powered by trogon & textual__

## Setup
1. Install requirements: `pip install -r requirements.txt`
2. Copy `config.example.py` to `config.py`
3. Get your telegram `api_id` and `api_hash` from https://my.telegram.org and copy them to `config.py`
4. Write your channel names or ids to `config.py`. If the song details in a channel are written as text in the song messages, you can add a regex to extract the song name and artist, like written in `config.example.py`

## Howto
Use `python main.py tui` to use the trogon interface and learn all commands and parameters

### Commands

#### `update`
- update the song database of your channels
- pass a channel name from your config with `--channel_name`
- if you dont specify a channel name, all channels get updates
- depending on the amount of songs in a channel, this can take some time

#### `search`
- search for artists or songnames
- interactively select songs from your search to download


## Todo:
- implement a full textual interface
- implement download after search non-hacky
- implement `download_all` for search command
- save if a song was already downloaded
- make it possible to save songs in categories and extract category information from songs
