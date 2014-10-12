#!/Users/oliv/anaconda/bin/python

import tweepy
import pandas as pd
from geopy import Nominatim
import folium

import time
import os
import sys
import webbrowser

from cred import *


def retrieve_contacts(api):
    # using list comprehension to extract followers informations
    l_follow = [it for it in tweepy.Cursor(api.followers, count=200).items()]
    l_friends = [it for it in tweepy.Cursor(api.friends, count=200).items()]
    return (l_follow, l_friends)


def populate_df(l_follow, l_friends):
    df_follow_all = pd.DataFrame([[it._json['name'], it._json['location']]
                                  for it in l_follow],
                                 columns=['name', 'location'])
    df_friends_all = pd.DataFrame([[it._json['name'], it._json['location']]
                                   for it in l_friends],
                                  columns=['name', 'location'])

    # removing mutual follows from followers and putting them in a separate list
    mask_follow = df_follow_all['name'].isin(df_friends_all.name)
    df_mutual = df_follow_all[mask_follow]
    df_follow = df_follow_all[~mask_follow]

    # removing mutual follows from friends
    mask_friends = df_friends_all['name'].isin(df_follow_all.name)
    df_friends = df_friends_all[~mask_friends]

    # adding column with type follower, following or mutual
    df_friends['relation'] = 'following'
    df_follow['relation'] = 'follower'
    df_mutual['relation'] = 'mutual'

    df = pd.concat([df_friends, df_follow, df_mutual], ignore_index=True)
    return df


# sometimes nominatim has hiccups and misses locations
# if there are too many we need to relaunch this function
def geolocate_contacts(df):
    geolocator = Nominatim()
    df['lat'] = float('nan')
    df['lon'] = float('nan')
    min_wait = 1.0
    cnt = 0
    num_entries = len(df)
    for idx, it in enumerate(df['location'][:20]):
        sys.stdout.write("\rProcessing user # %d of %d\r"
                         % (idx+1, num_entries))
        sys.stdout.flush()
        if it != '':
            # avoids interrupting the loop by time-out errors
            try:
                # we also limit the rate of request to one per second
                # which is the maximum tolerated by nominatim
                t0 = time.clock()
                location = geolocator.geocode(df.location[idx].encode('utf-8'),
                                              exactly_one=True,
                                              timeout=5)
                t1 = time.clock()
                dt = min_wait - (t1 - t0)
                if dt > 0:
                    time.sleep(dt)
            except:
                location = None

            if location is not None:
                df.lat[idx] = location.latitude
                df.lon[idx] = location.longitude
                cnt = cnt + 1
    print "%d successful geolocations among %d"\
        % (cnt, len(df[df['location'] != '']))


def populate_map(df, map_folium, color):
    from math import isnan
    color_choice = {'following': '#ff0000', 'follower': '#00cc00',
                    'mutual': '#0000ff'}
    cnt = 0
    for key, grp in df.groupby(['lat', 'lon']):

        lat = key[0]
        lon = key[1]

        # adding html return characters between lines
        s = '<br>'.join(grp.name + ', ' + grp.location
                        + ' (' + grp.relation + ')')

        # convert to html leaflet.js readable string
        try:
            name = str(s.encode('ascii', 'xmlcharrefreplace'))
        except:
            print s + "encoding failed"
            name = "unknown"

        if not(isnan(lat)) and not(isnan(lon)):
            cnt = cnt + len(grp)
            if len(grp) == 1:
                color = color_choice[grp.relation.iloc[0]]
                map_folium.polygon_marker(location=[lat, lon],
                                          radius=4,
                                          line_color=color,
                                          fill_color=color,
                                          fill_opacity=0.7,
                                          line_opacity=0.9,
                                          popup=name)
            else:
                if (grp.relation == 'mutual').sum() > 0:
                    color = color_choice['mutual']
                elif (grp.relation == 'follower').sum() > 0:
                    color = color_choice['follower']
                else:
                    color = color_choice['following']
                map_folium.circle_marker(location=[lat, lon],
                                         radius=1000*len(grp),
                                         line_color=color,
                                         fill_color=color,
                                         fill_opacity=0.7,
                                         popup=name)
    print "%d known locations among %d" % (cnt, len(df))


def main():

    print "------- Tweemap.py -------"
    print "Authentication"
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    print "Retrieving the list of your contacts with tweepy"
    fname = "twitter_contacts.json"
    bool_load = False
    df = pd.DataFrame(columns=['name', 'location', 'relation'])
    if os.path.isfile(fname):
        print "A file of your contacts already exists."
        s = raw_input("Load it or use api calls? (Y|n)")
        if s.lower() != 'n':
            bool_load = True
            df = pd.read_json(fname)

    if not bool_load:
        l_follow, l_friends = retrieve_contacts(api)
        df = populate_df(l_follow, l_friends)
        print "Contacts retrieved."
        print "Write data as a file?"
        print "WARNING: old file will be overwritten!"
        s = raw_input("(Y|n)")
        if s.lower() != 'n':
            df.to_json(fname)

    num_loc = len(df[df['location'] != ''])
    print "%d / %d of your contacts gave their location" % (num_loc, len(df))
    print "Geolocating your contacts with geopy"
    geolocate_contacts(df)
    num_geoloc = len(df[df['lat'].notnull()])
    print "%d / %d of your contacts were geolocated" % (num_geoloc, len(df))
    print "Creating the map"
    map_usr = folium.Map(location=[20, -10], zoom_start=2,
                         tiles=(r"http://{s}.tile.thunderforest.com/"
                                "landscape/{z}/{x}/{y}.png"),
                         attr=('&copy; <a href="http://www.opencyclemap.org">'
                               'OpenCycleMap</a>,'
                               '&copy; <a href="http://openstreetmap.org">'
                               'OpenStreetMap</a> contributors,'
                               '<a href="http://creativecommons.org/'
                               'licenses/by-sa/2.0/">CC-BY-SA</a>'))
    populate_map(df, map_usr, '#f6546a')

    map_file = 'map.html'
    map_usr.create_map(map_file)
    webbrowser.open('file://'+os.getcwd()+'/'+map_file, new=1)


if __name__ == "__main__":
    main()
