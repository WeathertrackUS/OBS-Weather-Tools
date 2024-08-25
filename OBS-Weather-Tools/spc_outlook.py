import os
import requests
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import geopandas as gpd
import contextily as ctx
import logging as log
import feedparser
import tkinter as tk
import time

from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from tkinter import messagebox

matplotlib.use("TkAgg")

root = tk.Tk()
root.withdraw()

log_directory = 'C:\\log'
current_directory = os.path.dirname(os.path.abspath(__file__))
rss_url = 'https://www.spc.noaa.gov/products/spcacrss.xml'
check_interval = 60
refresh_interval = 15  # Refresh the list every 15 seconds
notified_titles = []  # List to store notified titles
first_message_title = None  # Title of the first message encountered

if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log.basicConfig(
    level=log.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='C:\\log\\obs-wx-tools-spc.log',
    filemode='w'
)


def check_rss_feed(url, interval):
    """
    Checks the RSS feed at the specified URL for new entries and sends a notification for each new entry.

    Parameters:
        url (str): The URL of the RSS feed to check.
        interval (int): The interval in seconds to wait between checks.
        refresh_interval (int): The interval in seconds to refresh the list of notified titles.

    Returns:
        None
    """
    last_refresh_time = time.time()  # Time of the last refresh

    while True:
        current_time = time.time()
        if current_time - last_refresh_time >= refresh_interval:
            # Refresh the list every refresh_interval seconds
            last_refresh_time = current_time

        feed = feedparser.parse(url)
        if feed.entries:
            for entry in feed.entries:
                # Check if the message is new
                if entry.title not in notified_titles:
                    # Process the message here
                    # For example, send a notification
                    truncated_title = entry.title[:256]
                    log.info(f'RSS - New RSS Notification. {entry.title}')  # skipcq: PYL-W1203
                    notification.notify(  # type: ignore
                        title="New RSS Feed Update",
                        message=(f'{truncated_title}. Check it out in the App!'),
                        timeout=10
                    )
                    # Add the title to the notified_titles list
                    notified_titles.append(entry.title)
        log.info(f'RSS - {notified_titles}')  # skipcq: PYL-W1203
        time.sleep(interval)
        log.info('RSS - Interval Passed')


def fetch_outlook(outlook_type):
    """
    Fetches a SPC Outlook based on the specified outlook type.

    Parameters:
        outlook_type (str): The type of outlook to fetch. Valid options are 'cat', 'tor', 'wind', and 'hail'.

    Returns:
        dict: The JSON data of the fetched outlook.

    Raises:
        requests.exceptions.RequestException: If the request to the URL fails.
        ValueError: If the outlook_type is not one of the valid options.
    """
    log.info('SPC Outlook - Fetching a SPC Outlook')
    if outlook_type == 'cat':
        url = 'https://www.spc.noaa.gov/products/outlook/day1otlk_cat.nolyr.geojson'
    elif outlook_type == 'tor':
        url = 'https://www.spc.noaa.gov/products/outlook/day1otlk_torn.nolyr.geojson'
    elif outlook_type == 'wind':
        url = 'https://www.spc.noaa.gov/products/outlook/day1otlk_wind.nolyr.geojson'
    elif outlook_type == 'hail':
        url = 'https://www.spc.noaa.gov/products/outlook/day1otlk_hail.nolyr.geojson'
    else:
        log.error('SPC Outlook - Invalid Outlook Type. outlook_type = ' + outlook_type)
        popup('Invalid Outlook Type. outlook_type = ' + outlook_type)

    response = requests.get(url)  # Requests the data from the GeoJSON URL
    response.raise_for_status()
    outlook_data = response.json()
    return outlook_data  # Returns the data from the Outlook


def create_output_directory():
    """
    Creates an output directory in the specified current directory.

    Parameters:
        current_directory (str): The path of the current directory.

    Returns:
        str: The path of the newly created output directory.
    """
    log.info('running create_output_directory')
    output_directory = os.path.join(current_directory, '../output')
    os.makedirs(output_directory, exist_ok=True)
    return output_directory


def setup_plot():
    """
    Sets up a plot with a specified size and aspect ratio.

    Returns:
        fig (matplotlib.figure.Figure): The figure object.
        ax (matplotlib.axes.Axes): The axes object.
    """
    log.info('running setup_plot')
    fig, ax = plt.subplots(figsize=(10, 8))  # Set the size of the plot
    fig.set_facecolor('black')
    ax.set_aspect('auto', adjustable='box')
    return fig, ax  # Return the variables holding the data about the plot


def set_plot_limits(ax):
    """
    Sets the x and y limits of a plot.

    Parameters:
        ax (matplotlib.axes.Axes): The axes object to set the limits for.

    Returns:
        None
    """
    log.info('running set_plot_limits')
    ax.set_xlim([-125, -66])  # Base for x: (-125, -66)
    ax.set_ylim([20, 60])  # Base for y: (23, 50)


def remove_axes_labels_boxes_title(ax):
    """
    Removes axes, labels, boxes, and titles from a plot.

    Parameters:
        ax (matplotlib.axes.Axes): The axes object to modify.

    Returns:
        None
    """
    log.info('running remove_axes_labels_boxes_title')
    # Remove the Axes
    ax.set_xticks([])
    ax.set_yticks([])

    # Remove the Labels
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    # Remove the Box around the Plot
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    # Remove the Title
    plt.title('')


def add_overlays(ax, outlook_type):
    """
    Adds overlays and shapefiles to a plot.

    Parameters:
        ax (matplotlib.axes.Axes): The axes object to add overlays to.
        current_directory (str): The path of the current directory.
        type (str): The type of header image to add.

    Returns:
        None
    """
    log.info('Adding all Overlays and Shapefiles')

    # State Outlines
    states_shapefile = os.path.join(current_directory, '../files/mapping/s_11au16.shp')
    states = gpd.read_file(states_shapefile)
    states.plot(ax=ax, edgecolor='black', lw=0.75, alpha=0.75)
    ax.set_facecolor("black")  # Background of the CONUS Shapefile will be Black

    # Interstate Lines
    highways_shapefile = os.path.join(current_directory, '../files/mapping/USA_Freeway_System.shp')
    highways_gdf = gpd.read_file(highways_shapefile)
    highways_gdf.plot(ax=ax, color='red', linewidth=0.6, alpha=0.75)

    # Header Image
    if outlook_type == 'cat':
        header_img = plt.imread(os.path.join(current_directory, '../files/overlays/wtus_cat_header.png'))
    elif outlook_type == 'tor':
        header_img = plt.imread(os.path.join(current_directory, '../files/overlays/wtus_tor_header.png'))
    elif outlook_type == 'wind':
        header_img = plt.imread(os.path.join(current_directory, '../files/overlays/wtus_wind_header.png'))
    elif outlook_type == 'hail':
        header_img = plt.imread(os.path.join(current_directory, '../files/overlays/wtus_hail_header.png'))
    elif outlook_type == 'd4-8':
        header_img = plt.imread(os.path.join(current_directory, '../files/overlays/wtus_d48_header.png'))
    elif outlook_type == 'prob':
        header_img = plt.imread(os.path.join(current_directory, '../files/overlays/wtus_prob_header.png'))
    else:
        log.error('Header Error. Outlook_type ' + outlook_type + 'Error on line 429')
        popup('error', 'Header Error', 'An error has occured getting the header image. The program will now quit.')
    header_img = OffsetImage(header_img, zoom=0.4)
    ab = AnnotationBbox(header_img, (0.3, 0.95), xycoords='axes fraction', frameon=False)
    ax.add_artist(ab)


def add_basemap(ax):
    """
    Adds a basemap to a plot.

    Parameters:
        ax (matplotlib.axes.Axes): The axes object to add the basemap to.

    Returns:
        None
    """
    log.info('running add_basemap')
    ctx.add_basemap(ax, zoom=6, crs='EPSG:4326', source='https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png?api_key=63fe7729-f786-444d-8787-817db15f3368')  # type: ignore  # skipcq: FLK-E501
    log.info('basemap loaded')


def check_outlook_availability(outlook_data):
    """
    Checks if there is an available outlook in the given outlook data.

    Parameters:
        outlook_data (dict): The outlook data to check for availability.

    Returns:
        bool: True if an outlook is available, False otherwise.
    """
    log.info('running check_outlook_availability')
    for feature in outlook_data['features']:
        # Check is there is a LABEL if there is coordinates in the geometry portion of the feature from the Source
        if 'coordinates' in feature['geometry']:
            log.info('There is an outlook')
            return True
    return False


def plot_outlook_polygons(ax, outlook_type, outlook_data):  # skipcq: PY-R1000
    """
    Plots outlook polygons on a given axis.

    Parameters:
        ax (matplotlib.axes.Axes): The axis to plot the outlook polygons on.
        outlook_type (str): The type of outlook to plot (e.g. 'cat', 'tor', 'wind', etc.).
        outlook_data (dict): A dictionary containing the outlook data, including features and geometry.

    Returns:
        None
    """
    log.info('Plotting Outlook Polygons')
    if outlook_type == 'cat':
        for feature in outlook_data['features']:
            outlook_label = feature['properties']['LABEL']
            outlook_polygon = feature['geometry']['coordinates']
            if feature['geometry']['type'] == 'Polygon':
                outlook_polygon = [outlook_polygon]  # Convert single polygon to a list for consistency
            for polygon in outlook_polygon:  # Find the properties of each polygon
                ax.add_patch(mpatches.Polygon(polygon[0], alpha=0.5, ec='k', lw=1, fc=color('cat', outlook_label)))
    elif outlook_type == 'tor':
        for feature in outlook_data['features']:
            outlook_label = feature['properties']['LABEL']
            outlook_polygon = feature['geometry']['coordinates']
            if feature['geometry']['type'] == 'Polygon':
                outlook_polygon = [outlook_polygon]  # Convert single polygon to a list for consistency
                for polygon in outlook_polygon:  # Find the properties of each polygon
                    if outlook_label == 'SIGN':  # Add hatching for 'SIGN' outlook type
                        ax.add_patch(mpatches.Polygon(polygon[0], alpha=0.2, ec='k', lw=1, fc=color('tor', outlook_label),
                                                      edgecolor='black', hatch='x'))
                    else:
                        ax.add_patch(mpatches.Polygon(polygon[0], alpha=0.5, ec='k', lw=1, fc=color('tor', outlook_label)))
            elif feature['geometry']['type'] == 'MultiPolygon':
                outlook_polygon = [outlook_polygon]  # Convert single polygon to a list for consistency
                for multipolygon in outlook_polygon:  # Find the properties of each polygon
                    for polygon in multipolygon:
                        if outlook_label == 'SIGN':  # Add hatching for 'SIGN' outlook type
                            ax.add_patch(mpatches.Polygon(polygon[0], alpha=0.2, ec='k', lw=1, fc=color('tor', outlook_label),
                                                          edgecolor='black', hatch='x'))
                        else:
                            ax.add_patch(mpatches.Polygon(polygon[0], alpha=0.5, ec='k', lw=1, fc=color('tor', outlook_label)))
    elif outlook_type == 'wind':
        for feature in outlook_data['features']:
            outlook_label = feature['properties']['LABEL']
            outlook_polygon = feature['geometry']['coordinates']
            if feature['geometry']['type'] == 'Polygon':
                outlook_polygon = [outlook_polygon]  # Convert single polygon to a list for consistency
                for polygon in outlook_polygon:  # Find the properties of each polygon
                    if outlook_label == 'SIGN':  # Add hatching for 'SIGN' outlook type
                        ax.add_patch(mpatches.Polygon(polygon[0], alpha=0.2, ec='k', lw=1, fc=color('wind', outlook_label),
                                                      edgecolor='black', hatch='x'))
                    else:
                        ax.add_patch(mpatches.Polygon(polygon[0], alpha=0.5, ec='k', lw=1, fc=color('wind', outlook_label)))
            elif feature['geometry']['type'] == 'MultiPolygon':
                outlook_polygon = [outlook_polygon]  # Convert single polygon to a list for consistency
                for multipolygon in outlook_polygon:  # Find the properties of each polygon
                    for polygon in multipolygon:
                        if outlook_label == 'SIGN':  # Add hatching for 'SIGN' outlook type
                            ax.add_patch(mpatches.Polygon(polygon[0], alpha=0.2, ec='k', lw=1, fc=color('wind', outlook_label),
                                                          edgecolor='black', hatch='x'))
                        else:
                            ax.add_patch(mpatches.Polygon(polygon[0], alpha=0.5, ec='k', lw=1, fc=color('wind', outlook_label)))
    elif outlook_type == 'hail':
        for feature in outlook_data['features']:
            outlook_label = feature['properties']['LABEL']
            outlook_polygon = feature['geometry']['coordinates']
            if feature['geometry']['type'] == 'Polygon':
                outlook_polygon = [outlook_polygon]  # Convert single polygon to a list for consistency
                for polygon in outlook_polygon:  # Find the properties of each polygon
                    if outlook_label == 'SIGN':  # Add hatching for 'SIGN' outlook type
                        ax.add_patch(mpatches.Polygon(polygon[0], alpha=0.2, ec='k', lw=1, fc=color('hail', outlook_label),
                                                      edgecolor='black', hatch='x'))
                    else:
                        ax.add_patch(mpatches.Polygon(polygon[0], alpha=0.5, ec='k', lw=1, fc=color('hail', outlook_label)))
            elif feature['geometry']['type'] == 'MultiPolygon':
                outlook_polygon = [outlook_polygon]  # Convert single polygon to a list for consistency
                for multipolygon in outlook_polygon:  # Find the properties of each polygon
                    for polygon in multipolygon:
                        if outlook_label == 'SIGN':  # Add hatching for 'SIGN' outlook type
                            ax.add_patch(mpatches.Polygon(polygon[0], alpha=0.2, ec='k', lw=1, fc=color('hail', outlook_label),
                                                          edgecolor='black', hatch='x'))
                        else:
                            ax.add_patch(mpatches.Polygon(polygon[0], alpha=0.5, ec='k', lw=1, fc=color('hail', outlook_label)))
    else:
        log.error('Plotting Error. Outlook_Type' + outlook_type + 'error on line 598')
        popup('error', 'Plotting Error', 'An error has occured plotting the outlook. The program will now quit.')


def no_outlook_available():  # skipcq: PYL-R1711
    """
    Displays an error message when no severe weather outlook is available.

    Parameters:
        None

    Returns:
        None

    Logs:
        info: No outlook available
    """
    log.info('There is no outlook available')
    popup('warning', 'No Outlook', "There is no outlook available at this time")
    return  # skipcq: PYL-R1711


def display_outlook(outlook_type, outlook_data):
    """
    Displays the categorical outlook for a given day.

    Parameters:
        day (int): The day for which to display the outlook.
        outlook_data (dict): The data containing the outlook information.

    Returns:
        None
    """
    log.info('Displaying Categorial Outlook')
    fig, ax = setup_plot()

    # Clear the figure and axes before displaying a new outlook
    fig.clear()
    ax = fig.add_subplot(111)

    if not check_outlook_availability(outlook_data):
        no_outlook_available()

    add_overlays(ax, outlook_type)
    set_plot_limits(ax)
    add_basemap(ax)
    remove_axes_labels_boxes_title(ax)

    plot_outlook_polygons(ax, outlook_type, outlook_data)

    output_directory = create_output_directory()
    output_filename = f'spc_day_1_{outlook_type}_outlook.png'
    output_path = os.path.join(output_directory, output_filename)

    log.info('Showing the plot')
    plt.savefig(output_path, dpi=96, bbox_inches='tight')


def color(outlook_type, outlook_level):
    # skipcq: FLK-W505
    """
    Returns the color associated with a given outlook type.

    Parameters:
        type (str): The type of outlook (e.g., 'cat', 'tor', 'wind', 'hail', 'prob', 'd4-8').
        outlook_type (str): The specific outlook type (e.g., 'TSTM', 'MRGL', 'SLGT', 'ENH', 'MDT', 'HIGH', '0.02', '0.05', '0.10', '0.15', '0.30', '0.45', '0.60', 'sig').  # skipcq: FLK-W505

    Returns:
        str: The color associated with the given outlook type, or 'blue' if not found.
    """
    log.info('Getting ' + outlook_level + ' for ' + outlook_type + ' outlook')
    if outlook_type == 'cat':
        colors = {
            'TSTM': 'lightgreen',
            'MRGL': 'green',
            'SLGT': 'yellow',
            'ENH': 'orange',
            'MDT': 'red',
            'HIGH': 'magenta'
        }
    if outlook_type == 'tor':
        colors = {
            '0.02': 'green',
            '0.05': 'brown',
            '0.10': 'yellow',
            '0.15': 'red',
            '0.30': 'pink',
            '0.45': 'purple',
            '0.60': 'blue',
            'sig': 'black'
        }
    if outlook_type in ('wind', 'hail'):
        colors = {
            '0.05': 'saddlebrown',
            '0.15': 'gold',
            '0.30': 'red',
            '0.45': 'fuchsia',
            '0.60': 'blueviolet',
            'sig': 'black'
        }
    if outlook_type not in ('cat', 'tor', 'wind', 'hail'):
        log.error("There was an error accessing colors. Error on line 751")
        popup('warning', 'Invalid Outlook Type', 'There was an error when trying to get colors. The program will now quit.')

    return colors.get(outlook_level, 'blue')  # Returns the color, blue if not found


def popup(popup_type, title, message):  # skipcq: PYL-R1710
    """
    The `popup` function displays different types of popups based on the input parameters such as
    info, error, warning, or question.

    :param type: The `type` parameter in the `popup` method specifies the type of popup to display.
    :param title: The `title` parameter in the `popup` function refers to the title of the popup
    window that will be displayed. It is the text that appears at the top of the popup window to
    provide context or information about the message being shown to the user.
    :param message: The `message` parameter in the `popup` function is the text that will be
    displayed in the popup dialog box. It is the information, error message, warning message, or
    question that you want to show to the user depending on the type of popup being displayed.
    :return: The `popup` method returns the value of `question` when the `type` parameter is
    set to 'question'.
    """
    log.info('Showing a ' + popup_type + ' popup titled ' + title + 'with the following message: ' + message)
    if popup_type == 'info':
        messagebox.showinfo(title, message)
    elif popup_type == 'error':
        messagebox.showerror(title, message)
    elif popup_type == 'warning':
        messagebox.showwarning(title, message)
    elif popup_type == 'question':
        global question  # skipcq: PYL-W0603
        question = messagebox.askquestion(title, message)
        return question  # skipcq: PYL-R1710
    else:
        messagebox.showerror('Invalid Popup', 'There was an error when trying to display a popup. The program will now quit.')


def kickstart():
    """
    The `kickstart` function initializes and displays various types of weather outlook data.
    
    It fetches the outlook data for 'cat', 'tor', 'wind', and 'hail' using the `fetch_outlook` function.
    
    Then, it displays the outlook data for each type using the `display_outlook` function.
    
    :return: None
    """
    cat_outlook_data = fetch_outlook('cat')
    tor_outlook_data = fetch_outlook('tor')
    wind_outlook_data = fetch_outlook('wind')
    hail_outlook_data = fetch_outlook('hail')

    display_outlook('cat', cat_outlook_data)
    display_outlook('tor', tor_outlook_data)
    display_outlook('wind', wind_outlook_data)
    display_outlook('hail', hail_outlook_data)
