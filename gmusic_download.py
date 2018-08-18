"""
Usage: gmusic-download.py <artist> <album>
"""
from __future__ import print_function
import os
import re
import sys
import unicodedata

from docopt import docopt
from gmusicapi import Mobileclient
import magic
import requests
from tqdm import tqdm

FFMPEG_CMD='ffmpeg'
FFMPEG_ARGS = [
        '-loglevel', 'error',
        '-i', '{input}',
        '-b:a', '320k',
        '-metadata', 'title="{title}"',
        '-metadata', 'artist="{artist}"',
        '-metadata', 'album="{album}"',
        '-metadata', 'track="{track}"',
        '-f', 'mp3', '{output}']

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    value = unicode(re.sub('[-\s]+', '-', value))
    return value

def download_album(username, password, artist_name, album_name):
    api = Mobileclient()
    api.login(username, password, Mobileclient.FROM_MAC_ADDRESS)

    library = api.get_all_songs()
    songs = [s for s in library if s['albumArtist'] == artist_name and s['album'] == album_name]

    if len(songs) == 0:
        print('Error: Album not found', file=sys.stderr)
        return

    device_id = api.get_registered_devices()[0]['id'].replace('0x', '')
    dname = slugify(unicode(album_name))
    os.mkdir(dname)
    
    # download songs
    for song in tqdm(songs, desc='Downloading'):
        fname = slugify(song['title'])
        mpg_name = os.path.join(dname, fname + '.mpg')
        mp3_name = os.path.join(dname, fname + '.mp3')

        url = api.get_stream_url(song['id'], device_id=device_id)
        response = requests.get(url)

        # first save as MPEG video
        with open(mpg_name, 'wb') as fout:
            for chunk in response.iter_content(chunk_size=128):
                fout.write(chunk)

        # call FFMPEG to convert to MP3
        os.system(' '.join([FFMPEG_CMD] + FFMPEG_ARGS).format(
            input=mpg_name,
            output=mp3_name,
            title=song['title'],
            artist=song['albumArtist'],
            album=song['album'],
            track=song['trackNumber']))

        os.remove(mpg_name)

    # download album art
    art_name = os.path.join(dname, dname + '.png')
    album_info = api.get_album_info(songs[0]['albumId'], include_tracks=False)
    response = requests.get(album_info['albumArtRef'])
    t = magic.from_buffer(response.content, mime=True)

    if t == 'image/jpeg':
        ext = '.jpg'
    elif t == 'image/png':
        ext = '.png'
    else:
        print('Unknown MIME type: {}'.format(t), file=sys.stderr)
        ext = '.wat'

    with open(os.path.join(dname, dname + ext), 'wb') as fout:
        fout.write(response.content)

if __name__ == '__main__':
    args = docopt(__doc__)

    with open('login.txt') as f:
        username, password = f.read().split()

    download_album(username, password, args['<artist>'], args['<album>'])

