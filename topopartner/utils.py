"""General utilities for the topopartner module.
"""

# pylint: disable=E0401,E1101
import io
import re
import math
import logging
import requests
import numpy
import gpxpy.gpx
from . import models


LOGGER = logging.getLogger(__name__)


def gather_map_data(request):
    """Gather basic data for the creation of the Leafleat map. Plots the map
    with the waypoints from the database, with bounds to fit them.
    """
    data = {
        "waypoints": list(),
        "categories": models.WaypointCategory.objects.filter(user=request.user)
    }
    count, lats, lngs = 0, list(), list()
    for waypoint in models.Waypoint.objects.filter(user=request.user):
        count += 1
        data["waypoints"].append(waypoint)
        lats.append(waypoint.latitude)
        lngs.append(waypoint.longitude)
    if count == 0:
        data["center"] = {"lat": 48.867, "lng": 2.3265}
        data["bounds"] = {
            "sw": [43.3911, -1.658611111],
            "ne": [49.1203, 6.1778],
        }
        return data
    data["center"] = {
        "lat": sum(lats) / count,
        "lng": sum(lngs) / count
    }
    data["bounds"] = {
        "sw": [min(lats), min(lngs)],
        "ne": [max(lats), max(lngs)]
    }
    return data


def distance(lat1, lon1, lat2, lon2):
    # pylint: disable=C0103
    """Compute the distance in meters between two points.
    """
    r = 6371000
    phi1 = lat1 * math.pi / 180.
    phi2 = lat2 * math.pi / 180.
    delta_phi = (lat2 - lat1) * math.pi / 180.
    delta_lambda = (lon2 - lon1) * math.pi / 180.
    a = math.sin(.5 * delta_phi) * math.sin(.5 * delta_phi)\
        + math.cos(phi1)\
        * math.cos(phi2)\
        * math.sin(.5 * delta_lambda)\
        * math.sin(.5 * delta_lambda)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = r * c
    return d


def _fetch_elevation_data_gpsvisualizer(track):
    url = "https://www.gpsvisualizer.com/convert?output_elevation"
    payload = {
        "convert_delimiter": "tab",
        "add_elevation": "auto",
        "profile_x": "distance",
        "profile_y": "altitude",
        "remote_data": "",
        "submitted": "Convert & add elevation",
        "convert_format": "gpx",
        "units": "metric"
    }
    files = [
        ("uploaded_file_1", io.BytesIO(track.gpx.encode()))
    ]
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    if response.status_code != 200:
        LOGGER.error("Could not fetch elevation data from GPS Visualizer.")
        return None
    match = re.search(r"download/convert/.*?\.gpx", response.text)
    if match is None:
        LOGGER.error("Invalid response from GPS Visualizer (could not find GPX download link).")
        return None
    response = requests.get("https://www.gpsvisualizer.com/" + match.group(0))
    if response.status_code != 200:
        LOGGER.error("Could not download GPX from GPS Visualizer.")
        return None
    return response.text


def fetch_elevation_data(track):
    """Add elevation data to a track. Return `True` on success.
    """
    xml = _fetch_elevation_data_gpsvisualizer(track)
    if xml is not None:
        track.gpx = xml
        track.save()
        return True
    return False


def compute_stats(track, save_values=False):
    """Compute the distance and the elevation profile of a track.
    """
    elevation_data = list()
    prev_lat, prev_lng, prev_ele = None, None, None
    dist, uphill, downhill = 0, 0, 0
    time_start, time_end = None, None
    for i, trkpt in enumerate(track.iter_trackpoints()):
        if i == 0:
            time_start = trkpt.time
        else:
            time_end = trkpt.time
            dist += distance(prev_lat, prev_lng, trkpt.latitude, trkpt.longitude)
        prev_lat = trkpt.latitude
        prev_lng = trkpt.longitude
        if trkpt.elevation is not None:
            if len(elevation_data) == 0:
                elevation_data.append([0, trkpt.elevation])
            else:
                diff_ele = trkpt.elevation - prev_ele
                if diff_ele > 0:
                    uphill += diff_ele
                else:
                    downhill -= diff_ele
                elevation_data.append([dist, trkpt.elevation])
            prev_ele = trkpt.elevation
    if save_values:
        track.distance = dist
        track.uphill = uphill
        track.downhill = downhill
        if time_start is not None and time_end is not None:
            track.duration = time_end - time_start
        track.save()
    return elevation_data


def latlngs_to_gpx(latlngs):
    """Convert a sequence of points into a GPX track.
    """
    gpx = gpxpy.gpx.GPX()
    trk = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(trk)
    trkseg = gpxpy.gpx.GPXTrackSegment()
    trk.segments.append(trkseg)
    for latlng in latlngs:
        trkseg.points.append(gpxpy.gpx.GPXTrackPoint(
            latlng["lat"],
            latlng["lng"],
        ))
    return gpx


def linear_regression(tracks):
    """Fit a linear regression model for predicting duration.
    """
    features = numpy.zeros((len(tracks), 2))
    targets = numpy.zeros((len(tracks),))
    for i, track in enumerate(tracks):
        features[i, 0] = track.distance
        features[i, 1] = track.uphill
        targets[i] = track.duration.total_seconds()
    stacked = numpy.vstack([features.T, numpy.ones(len(features))]).T
    return numpy.linalg.lstsq(stacked, targets, rcond=None)[0]


def latlng_to_xy(lat, lng):
    # pylint: disable=C0103
    """Node constructor from latitude and longitude (in degrees) using a
    Mercator's projection approximation. This is hardcoded from
    https://github.com/ychalier/chaine-des-puys
    """
    scaler = {
        'target': 1000,
        'min_x': 344.832193287037,
        'max_x': 345.5064780092593,
        'min_y': 263.80521703818465,
        'max_y': 265.2623060625809,
        'aspect': 0.46276151349208056
    }
    w = 679.
    h = 724.
    theta = math.pi * lat / 180.
    phi = math.pi * lng / 180.
    x = w * (phi + math.pi) / (2 * math.pi)
    y = .5 * h - (w / (2 * math.pi))\
        * math.log(math.tan(.25 * math.pi + .5 * theta))
    return (
        (x - scaler["min_x"]) / (scaler["max_x"] - scaler["min_x"]) * scaler["target"],
        (y - scaler["min_y"]) / (scaler["max_y"] - scaler["min_y"])\
            * scaler["target"] / scaler["aspect"],
    )


def smooth(track, threshold):
    smoothed = [track[0]]
    for point in track:
        if distance(smoothed[-1].latitude, smoothed[-1].longitude, point.latitude, point.longitude) > threshold:
            smoothed.append(point)
    return smoothed


def gap(pt, pt_left, pt_right):
    x = numpy.array((pt_left.latitude, pt_left.longitude))
    y = numpy.array((pt.latitude, pt.longitude))
    z = numpy.array((pt_right.latitude, pt_right.longitude))
    u = y - x
    v = z - x
    proj = (numpy.dot(u, v) / numpy.sqrt(v.dot(v)) ** 2) * v
    return numpy.sqrt(proj.dot(proj))


def simplify(track, target):
    simplified = track[:]
    gaps = []
    for i, point in enumerate(simplified[:-1]):
        if i == 0:
            continue
        gaps.append(gap(point, simplified[i - 1], simplified[i + 1]))
    while len(simplified) > target:
        i = numpy.argmin(gaps)
        simplified.pop(i + 1)
        gaps.pop(i)
        if i > 0:
            gaps[i - 1] = gap(simplified[i], simplified[i - 1], simplified[i + 1])
        if i + 1 < len(gaps):
            gaps[i] = gap(simplified[i + 1], simplified[i], simplified[i + 2])
    return simplified
    

def clean(track, smoothing_threshold, simplification_target_proportion):
    """Smooth and simplify a track. More at
    https://www.gpsvisualizer.com/tutorials/track_filters.html
    
    Parameters
    ==========
    
        track: list[gpxpy.gpx.GPXTrackPoint]
            The list of points defining the track to clean.
            
        smoothing_threshold: float
            Only keep the points that are at least at this
            distance from their predecessor.
            
        simplification_target: float
            Proportion of points for the output track.
            
    Return
    ======
        list[gpxpy.gpx.GPXTrackPoint]
        The clean version of the input track.
        
    """
    return simplify(
        smooth(track, smoothing_threshold),
        simplification_target_proportion * len(track)
    )