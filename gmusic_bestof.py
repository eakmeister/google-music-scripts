"""
Usage: gmusic-download.py <artist> <album>
"""
from __future__ import print_function, unicode_literals
import os
import re
import sys
import unicodedata

from gmusicapi import Mobileclient
from tqdm import tqdm

def bestof(username, password):
    pass
    api = Mobileclient()
    api.login(username, password, Mobileclient.FROM_MAC_ADDRESS)

    library = api.get_all_songs()

    for year in range(2018, 2010, -1):
        songs = [s for s in library if 'year' in s and s['year'] == year]
        albums = set([(s['artist'], s['album']) for s in songs])

        plays = []
        for artist, album in albums:
            plays.append((sum([s['playCount'] if 'playCount' in s else 0 for s in songs if s['album'] == album]), artist, album)) 

        plays = sorted(plays, reverse=True)
        print('===== {} ====='.format(year))

        for play_count, artist, album in plays:
            print('{} - {} ({})'.format(artist, album, play_count))
        print()

if __name__ == '__main__':
    with open('login.txt') as f:
        username, password = f.read().split()

    bestof(username, password)

