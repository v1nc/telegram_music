# These example values won't work. You must get your own api_id and
# api_hash from https://my.telegram.org, under API Development.
api_id = 12345
api_hash = '0123456789abcdef0123456789abcdef'
channels = [
    {
        'name' : 'a_channel_name'
        'format' : r'(?P<artist>.*) - (?P<songname>.*).flac'
    }
]