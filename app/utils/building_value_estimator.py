import overpy
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from shapely.geometry import Polygon
from shapely.ops import transform
from pyproj import Transformer, CRS
from typing import Dict, Any, Optional


class BuildingEstimationError(Exception):
    """Custom exception for building value estimation errors."""

    pass


def geocode_address(address: str) -> Dict[str, float]:
    geolocator = Nominatim(user_agent="building_value_estimator")
    try:
        location = geolocator.geocode(address, timeout=10)
        if not location:
            raise BuildingEstimationError(f"Address not found: {address}")
        return {"lat": location.latitude, "lon": location.longitude}
    except (GeocoderServiceError, GeocoderTimedOut) as e:
        raise BuildingEstimationError(f"Geocoding failed: {str(e)}")


def fetch_building_from_osm(lat: float, lon: float) -> Dict[str, Any]:
    api = overpy.Overpass()
    # Query for building polygons within 50m of the geocoded point
    query = f"""
    (
      way["building"](around:50,{lat},{lon});
      relation["building"](around:50,{lat},{lon});
    );
    out body;
    >;
    out skel qt;
    """
    try:
        result = api.query(query)
    except Exception as e:
        raise BuildingEstimationError(f"OSM query failed: {str(e)}")

    # Prefer ways, then relations
    buildings = result.ways + result.relations
    if not buildings:
        raise BuildingEstimationError(
            "No building data found near the provided address."
        )

    # Find the building whose centroid is closest to the point
    from shapely.geometry import Point

    point = Point(lon, lat)
    min_dist = float("inf")
    best_building = None
    best_geom = None

    for b in buildings:
        try:
            coords = []
            if hasattr(b, "nodes") and b.nodes:
                coords = [(float(n.lon), float(n.lat)) for n in b.nodes]
            elif hasattr(b, "members") and b.members:
                # For relations, try to extract outer polygons
                for m in b.members:
                    if m.role == "outer" and hasattr(m, "resolve"):
                        way = m.resolve()
                        coords = [(float(n.lon), float(n.lat)) for n in way.nodes]
                        break
            if len(coords) < 3:
                continue
            poly = Polygon(coords)
            dist = poly.centroid.distance(point)
            if dist < min_dist:
                min_dist = dist
                best_building = b
                best_geom = poly
        except Exception:
            continue

    if not best_building or not best_geom:
        raise BuildingEstimationError(
            "Could not extract building geometry from OSM data."
        )

    return {
        "osm_element": best_building,
        "geometry": best_geom,
        "tags": getattr(best_building, "tags", {}),
    }


def project_to_utm(geometry: Polygon, lat: float, lon: float) -> Polygon:
    # Determine UTM zone from lon/lat
    utm_crs = CRS.from_proj4(
        f"+proj=utm +zone={utm_zone(lon)} +datum=WGS84 +units=m +no_defs"
    )
    wgs84 = CRS.from_epsg(4326)
    transformer = Transformer.from_crs(wgs84, utm_crs, always_xy=True)
    return transform(transformer.transform, geometry)


def utm_zone(lon: float) -> int:
    return int((lon + 180) / 6) + 1


def compute_area_perimeter(geometry: Polygon) -> (float, float):
    area = geometry.area  # in m^2
    perimeter = geometry.length  # in m
    return area, perimeter


def extract_building_height(tags: Dict[str, str]) -> Optional[float]:
    if "height" in tags:
        try:
            return float(tags["height"])
        except ValueError:
            pass
    if "building:levels" in tags:
        try:
            return float(tags["building:levels"]) * 3.0
        except ValueError:
            pass
    return None


def estimate_building_values(address: str) -> Dict[str, Any]:
    coords = geocode_address(address)
    building = fetch_building_from_osm(coords["lat"], coords["lon"])
    projected_geom = project_to_utm(building["geometry"], coords["lat"], coords["lon"])
    area, perimeter = compute_area_perimeter(projected_geom)
    height = extract_building_height(building["tags"])
    result = {
        "grundflaeche": round(area, 2),
        "gebaeudeumfang": round(perimeter, 2),
        "gebaeudehoehe": round(height, 2) if height is not None else None,
        "height_available": height is not None,
    }
    if not result["height_available"]:
        result["message"] = "Building height not available in OSM data."
    return result
