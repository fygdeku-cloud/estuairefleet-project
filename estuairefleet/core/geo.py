from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_M = 6_371_000


def is_valid_lat_lng(lat: float, lng: float) -> bool:
    return -90 <= float(lat) <= 90 and -180 <= float(lng) <= 180


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lng1, lat2, lng2 = map(radians, (float(a[0]), float(a[1]), float(b[0]), float(b[1])))
    d_lat = lat2 - lat1
    d_lng = lng2 - lng1
    value = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lng / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(sqrt(value))


def distance_point_to_segment_m(
    point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]
) -> float:
    """Approximation locale suffisamment précise pour le géorepérage urbain."""
    lat_scale = 111_320
    lng_scale = 111_320 * cos(radians(float(point[0])))
    px, py = float(point[1]) * lng_scale, float(point[0]) * lat_scale
    ax, ay = float(start[1]) * lng_scale, float(start[0]) * lat_scale
    bx, by = float(end[1]) * lng_scale, float(end[0]) * lat_scale
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return haversine_m(point, start)
    factor = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    closest = (ay + factor * dy, ax + factor * dx)
    return sqrt((py - closest[0]) ** 2 + (px - closest[1]) ** 2)


def distance_point_to_polyline_m(point: tuple[float, float], points: list[list[float]]) -> float:
    if not points:
        return float("inf")
    if len(points) == 1:
        return haversine_m(point, tuple(points[0]))
    return min(distance_point_to_segment_m(point, tuple(a), tuple(b)) for a, b in zip(points, points[1:]))
