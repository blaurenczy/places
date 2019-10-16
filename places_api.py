"""
@author: Balazs Laurenczy
@date: 2019-02-09
@description: helper functions to analyze the (geo-)data of the visited places
"""

import pandas as pd
import datetime
import re
import codecs
import logging

from lxml import html

from geopy.geocoders import Nominatim, ArcGIS
from geopy.extra.rate_limiter import RateLimiter


def read_file(file_name):
    """
    Reads in a KML file and stores its content in a DataFrame

    Arguments
        file_name:  the KML data file's name as a string

    Returns
        df:    the DataFrame containing the geodata
    """

    with codecs.open(file_name, encoding='utf-8') as f:
        kml = f.read()

    # decode and re-encode to UTF-8 after doing some replacements
    kml = kml.replace('mwm:', 'mwm_').encode('utf-8')

    # read the document as HTML/XML
    doc = html.fromstring(kml)

    # create the DataFrame and the coounter
    df = pd.DataFrame(columns=['name', 'timestamp', 'color', 'coords_long', 'coords_lat',
        'category', 'icon'])
    i = 0

    # parse the file for some relevant information
    for placemark in doc.cssselect('Document Placemark'):
        # parse out the main fields
        name = placemark.cssselect('name')[0].text
        timestamp = placemark.cssselect('TimeStamp when')[0].text
        color = placemark.cssselect('styleUrl')[0].text.replace('#placemark-', '')
        coords = placemark.cssselect('Point coordinates')[0].text
        coords_long, coords_lat = coords.split(',')
        # parse out the category, that can be several items
        category = []
        for featureType in placemark.cssselect('ExtendedData mwm_featureTypes'):
            for child in featureType:
                category.append(child.text)
        category = ';'.join(category)
        # parse out the icon, that can be empty
        icon = placemark.cssselect('ExtendedData mwm_icon')
        if len(icon) == 0: icon = ''
        else: icon = icon[0].text
        # append the row
        df.loc[i,:] = [name, timestamp, color, float(coords_long), float(coords_lat), category, icon]
        i += 1

    # create the set of coordinates on which one can apply the geocoder's reverse function
    df['coords_for_reverse'] = [[df['coords_lat'][i], df['coords_long'][i]] for i in range(len(df))]

    try:
        # fetch location data
        geolocator_Nominatim = Nominatim(user_agent="places")
        reverse_Nominatim = RateLimiter(geolocator_Nominatim.reverse, min_delay_seconds=2)
        df['location_Nominatim'] = df['coords_for_reverse'].apply(reverse_Nominatim, language='en')
    except:
        logging.error('Error while reverse geolocating with Nominatim')

    try:
        # fetch location data
        geolocator_ArcGIS = ArcGIS(user_agent="places")
        reverse_ArcGIS = RateLimiter(geolocator_ArcGIS.reverse, min_delay_seconds=2)
        df['location_ArcGIS'] = df['coords_for_reverse'].apply(reverse_ArcGIS)
    except:
        logging.error('Error while reverse geolocating with ArcGIS')

    return df
