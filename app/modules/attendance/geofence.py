from math import radians, sin, cos, sqrt, atan2
from app.config import settings

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def is_within_geofence(lat, lon):
    distance = haversine(lat, lon, settings.GEOFENCE_LAT, settings.GEOFENCE_LON)
    return distance <= settings.GEOFENCE_RADIUS_METERS
