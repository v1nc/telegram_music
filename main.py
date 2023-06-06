import config
import click
import pickle 
import os
import re
import sys
from trogon import tui
from telethon.sync import TelegramClient
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.events import Mount
from textual.widgets import Footer, Header, Pretty, SelectionList
from textual.widgets.selection_list import Selection

SAVED_DATA_FILE = 'data.pkl'
LIST_FILE = "list.pkl"
DOWNLOAD_DIR = 'downloads'
selection_app = None
selection_list = []

class SelectionListApp(App[None]):
    CSS_PATH = "table.css"
    BINDINGS = [
        ("d", "download()", "Download selected ongs"),
        ("a", "all()", "Select/Deselect all songs from the list")
    ]
    all_toggle = False
    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield selection_list
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(SelectionList).border_title = "Select songs to download:"

    def action_download(self) -> None:
        with open(LIST_FILE, 'wb') as f:
                    pickle.dump(self.query_one(SelectionList).selected, f)
        selection_app.exit()
        # this is very dirty :D
        os.execv(sys.executable, ['python', sys.argv[0], "download-search"])
        sys.exit(0)

    def action_all(self) -> None:
        if self.all_toggle:
            selection_list.deselect_all()
            self.all_toggle = False
        else:
            selection_list.select_all()
            self.all_toggle = True

def print_info(message):
    click.echo('['+ click.style('telegram_music', fg='green') + f']: {message}')

def print_error(message):
    click.echo('['+ click.style('telegram_music', fg='red') + f']: {message}')

def download_list():
    ''' Download all songs that are saved in the list file.'''
    print()
    if os.path.exists(LIST_FILE):
        with open(LIST_FILE, 'rb') as f:
            song_list = pickle.load(f)
            song_counter = 1
            for song in song_list:
                splitted = song.split("@")
                if len(splitted) == 2:
                    channel = splitted[0]
                    song_id = splitted[1]
                    print_info(f'Downloading song {song_counter}/{len(song_list)}')
                    download_song(channel,song_id)
                    song_counter+=1
                else:
                    print_error(f'list id invalid: {song}')
        os.remove(LIST_FILE)
    else:
        print_error("No songs to download. Use the search command first!2")

def fetch_messages(channel):
    ''' Fetch all songs from a channel and save the details '''
    print_info(f'Updating songs from channel \'{channel["name"]}\'')
    if not channel['name'] in data['channels']:
        data['channels'][channel['name']] = {
            'songs' : {},
            'last_message_id': 0
        }
    last_message_id = data['channels'][channel['name']]['last_message_id']
    message_count = 0
    song_count = 0
    for message in client.iter_messages(channel['name'],min_id=last_message_id):
            if message_count == 0:
                last_message_id = message.id

            if message.audio:
                songname = message.file.title
                artist = message.file.performer
                if songname == None or artist == None:
                    filename = os.path.splitext(message.file.name)
                    info = re.match(channel['format'], message.file.name)
                    if info == None:
                        songname = message.file.name
                        artist = ""
                    else:
                        artist = info.group('artist')
                        songname = info.group('songname')
                data['channels'][channel['name']]['songs'][message.id] = {
                    'songname' : songname,
                    'artist' : artist,
                    'size' : (int(message.file.size / 10000) / 100),
                    'filetype' : message.file.mime_type,
                    'channel': channel['name'],
                    'id': message.id
                    }
                song_count+=1
            message_count+=1
    data['channels'][channel['name']]['last_message_id'] = last_message_id
    print_info(f'Found {song_count} new songs in the channel \'{channel["name"]}\'.')

def update_channels(channel_name):
    '''Command to update songs of channels'''
    if channel_name == "all":
        for channel in config.channels:
            fetch_messages(channel)
            with open(SAVED_DATA_FILE, 'wb') as f:
                    pickle.dump(data, f)
    else:
        for channel in config.channels:
            if channel_name == channel['name']:
                fetch_messages(channel)
                with open(SAVED_DATA_FILE, 'wb') as f:
                    pickle.dump(data, f)

def download_song(channel_name, song_id):
    '''Download a song of the given channel and message id.'''
    try:
        song_id = int(song_id)
    except ValueError:
        return
    message = client.get_messages(channel_name, ids=song_id)

    path = message.download_media()
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.rename(path, f'{DOWNLOAD_DIR}/{path}')
    print_info(f'Download of song {song_id} finished.')

@tui()
@click.group()
def cli():
    pass

@cli.command()
def download_search():
    '''Download the songs you selected in your search.'''
    download_list()

@cli.command()
@click.option('--channel_name', default='all',
    help='The channel you want to update, \'all\' for all channels')
def update(channel_name):
    '''Update the song database.'''
    update_channels(channel_name)

@cli.command()
@click.option('--channel_name', required=True, help='The channel from where you want to download a song')
@click.option('--song_id', required=True, type=int, help='The id of the song')
def download(channel_name, song_id):
    '''Download a song.'''
    download_song(channel_name, song_id)

@cli.command()
@click.option('--songname', help='Search for a songname')
@click.option('--artist', help='Search for a artist')
@click.option('--channel_name', help='Search in a specific channel')
@click.option('--update_first', default=False, type=bool, help='Update songs before searching')
@click.option('--download_all', default=False, type=bool, help='Download all results')
def search(songname, artist, channel_name, update_first, download_all):
    global selection_app, selection_list
    '''Search for a song in the database.'''
    if update_first:
        if channel_name != None:
            update_channels(channel_name)
        else:
            update_channels('all')
    results = []
    for channel in data['channels']:
        if channel_name == None or channel == channel_name:
            for song in data['channels'][channel]['songs']:
                song = data['channels'][channel]['songs'][song]
                if ((songname == None or songname.lower() in song['songname'].lower()) and 
                    (artist == None or artist.lower() in song['artist'].lower())):
                    results.append(song)
    if len(results) == 0:
        print_info("No results.")
        return

    selection_list = SelectionList[str]()
    for result in results:
        selection_list.add_option(
            Selection(f"""{result['artist']} - {result['songname']}, size: {result['size']} MB,\
type: {result['filetype']}""", f"{result['channel']}@{result['id']}", False ))
    selection_app = SelectionListApp()
    selection_app.run()

if __name__ == '__main__':
    data = {}
    if os.path.exists(SAVED_DATA_FILE):
        with open(SAVED_DATA_FILE, 'rb') as f:
            data = pickle.load(f)
    else:
        data['channels'] = {}
    client = TelegramClient('telegram_music', config.api_id, config.api_hash)
    client.start()
    cli()