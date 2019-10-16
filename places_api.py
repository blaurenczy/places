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
    Args
        file_name (string): the KML data file's name as a string
    Returns
        df (DataFrame): the DataFrame containing the geodata
    """

    # read in the file with UTF-8 encoding
    logging.info('Reading file {}'.format(file_name))
    with codecs.open(file_name, encoding='utf-8') as f:
        kml = f.read().encode('utf-8')

    # read the document as HTML/XML
    logging.info('Converting to HTML')
    doc = html.fromstring(kml)

    # create the DataFrame and the coounter
    df = pd.DataFrame(columns=['name', 'timestamp', 'color', 'coords_long', 'coords_lat',
        'category', 'icon'])
    i = 0

    # parse the file for some relevant information
    logging.info('Parsing out placemarks')
    for placemark in doc.cssselect('Document Placemark'):
        # parse out the main fields
        name = placemark.cssselect('name')[0].text
        # check if the default name is the english name
        lang_elems = placemark.cssselect('ExtendedData')[0].getchildren()[0].getchildren()
        lang_codes = [elem.get('code') for elem in lang_elems]
        if 'en' in lang_codes:
            # get the english name
            en_name = [elem.text for elem in lang_elems if elem.get('code') == 'en'][0]
            if en_name != name:
                logging.debug('    Replacing default name with english name: "{}" (before: "{}")'
                    .format(en_name, name))
                name = en_name
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
        logging.debug('  Parsed out placemark: "{}" - "{}" - long. {} - lat.{}'
            .format(name, timestamp, coords_long, coords_lat))
        df.loc[i,:] = [name, timestamp, color, float(coords_long), float(coords_lat), category, icon]
        i += 1

    logging.info('Parsed out {} placemarks'.format(i))

    return df


def process(df):
    """
    Further processes the DataFrame to clean it up, add info, etc.
    Args
         df (DataFrame): the DataFrame to process, containing the geodata
    Returns
        df (DataFrame): the processed DataFrame, containing more geodata
    """

    logging.info('Processing DataFrame')

    # do the reverse geocoding to get city names, etc
    df_all = reverse_geocode(df)

    # get a "short list" of places, for calculating distances
    df_places = extract_place_list(df_all)

    # get distances between places
    df_places = calculate_distances(df_places)

    return df


def reverse_geocode(df):
    """
    Do the reverse geocoding on the coordinates to get more information about each place
    Args
         df (DataFrame): the DataFrame to process, containing the geodata
    Returns
        df (DataFrame): the processed DataFrame, containing more geodata
    """

    logging.info('Reverse geocoding')

    # create the set of coordinates on which one can apply the geocoder's reverse function
    df['coords_for_reverse'] = [[df['coords_lat'][i], df['coords_long'][i]] for i in range(len(df))]

    # only do the reverse geocoding if it's not already done
    if 'location_Nominatim' not in df.columns:
        try:
            # fetch location data
            geolocator_Nominatim = Nominatim(user_agent="places")
            reverse_Nominatim = RateLimiter(geolocator_Nominatim.reverse, min_delay_seconds=2)
            df['location_Nominatim'] = df['coords_for_reverse'].apply(reverse_Nominatim, language='en')
        except:
            logging.error('Error while reverse geolocating with Nominatim')
    else:
        logging.info('Skipping Nominatim reverse geocoding')

    # only do the reverse geocoding if it's not already done
    if 'location_ArcGIS' not in df.columns:
        try:
            # fetch location data
            geolocator_ArcGIS = ArcGIS(user_agent="places")
            reverse_ArcGIS = RateLimiter(geolocator_ArcGIS.reverse, min_delay_seconds=2)
            df['location_ArcGIS'] = df['coords_for_reverse'].apply(reverse_ArcGIS)
        except:
            logging.error('Error while reverse geolocating with ArcGIS')
    else:
        logging.info('Skipping ArcGIS reverse geocoding')

    return df


def extract_place_list(df):
    """
    [TO FILL]
    Args
         df (DataFrame): the DataFrame to process, containing the geodata
    Returns
        df (DataFrame): the processed DataFrame, containing more geodata
    """

    logging.info('Extracting place list')
    # df['city_Nominatim'] = df['location_Nominatim'].apply(lambda l: l.raw['address'].get('city'))
    # df['city_ArcGIS'] = df['location_ArcGIS'].apply(lambda l: l.raw['address'].get('city'))

    return df

def calculate_distances(df):
    """
    [TO FILL]
    Args
         df (DataFrame): the DataFrame to process, containing the geodata
    Returns
        df (DataFrame): the processed DataFrame, containing more geodata
    """

    logging.info('Calculating distances')

    return df
