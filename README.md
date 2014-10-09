# Tweemap.py

Map your twitter contacts !

![screenshot](https://raw.githubusercontent.com/odhondt/tweemap/master/screenshot.png)

This python script creates an interactive map of your twitter contacts and classifies them into 3 categories: following, follower and mutual. You can drag and zoom the map. Clicking on a marker opens a popup with user names, locations and relationships. If several users are located in the same spot, the marker is a circle with a radius proportinal to the number of contacts. The colors correspond to the relationship.

**Limitation:** due to the rate restriction imposed by twitter's api, only up to 3000 contacts can be displayed in this version.

**WARNING** use at your own risk. This version is not the final one, there are still some small bugs to fix.

* dependecies:
  * tweepy
  * pandas
  * geopy
  * folium

* usage:
  * change `cred_example.py` name into `cred.py`
  * register for a twitter application and fill in the variables with your credentials in `cred.py`
  * launch `python tweemap.py`. This might take a while depending on how many contacts you have.
  * In the end, a browser window with the map should open.

