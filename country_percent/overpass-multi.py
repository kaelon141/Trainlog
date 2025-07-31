import json
import multiprocessing as mp
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import floor
from time import time

import geopandas as gpd
import numpy as np
import osm2geojson
import pycountry
import requests
import shapely
from requests import JSONDecodeError
from shapely.geometry import LineString, MultiPolygon, Polygon, mapping, shape
from shapely.ops import split, unary_union

NUM_CORES = max(
    floor(mp.cpu_count() * 0.5 - 1), 1
)  # might get killed by the OS if it uses more than 50% of cores
RAIL_WIDTH_BUFFER_M = 50  # default = 50m
PRE_MERGE_PERCENTAGE = (
    0.5  # lower = faster but also lower = more likely to merge too much
)
POST_MERGE_MAX_AREA = (
    0.00000001  # 1e-11 (required to stop imperfect cuts from re-merging)
)
SIMPLIFY_TOLERANCE = 0.00002  #


def safe_process(arg):
    try:
        return process(arg)
    except Exception as e:
        print(f"[SAFE_PROCESS ERROR] {arg}: {e}")
        return None


def main(country_code, cores=NUM_CORES):
    files: list = []
    subdivisions = get_subdivisions(country_code)

    if subdivisions:
        print(
            f"[INFO] Using ProcessPoolExecutor with {min(cores, len(subdivisions))} workers"
        )
        with ProcessPoolExecutor(max_workers=min(cores, len(subdivisions))) as executor:
            # Submit all tasks
            future_to_subdivision = {
                executor.submit(safe_process, subdivision): subdivision
                for subdivision in subdivisions
            }

            # Collect results as they complete
            for future in as_completed(future_to_subdivision):
                subdivision = future_to_subdivision[future]
                try:
                    file = future.result()
                    print(f"[POOL RETURNED] {file}")
                    if file:
                        files.append(file)
                except Exception as exc:
                    print(
                        f"[ERROR] Subdivision {subdivision} generated an exception:\n{exc}"
                    )
    else:
        file = process(country_code, True)
        if file:
            files.append(file)

    # Load and collect feature data from files
    features = []
    for filepath in files:
        with open(filepath, "r") as file:
            data = json.load(file)
        features.extend(data["features"])

    export(country_code, features)


def export(country_code, features):
    # convert to gdf
    geometries = [shape(feature["geometry"]) for feature in features]
    gdf = gpd.GeoDataFrame(features, geometry=geometries, crs="EPSG:4326")
    # clip to country boundaries
    gdf = clip_to_boundary(gdf, fetch_country_boundary(country_code))
    # calculate polygon area
    data = calculate_area(gdf)
    # export to file
    processed_path = "countries/processed/ERROR.geojson"
    if len(country_code) == 2:
        processed_path = f"countries/processed/{country_code.lower()}.geojson"
    else:
        os.makedirs(f"countries/processed/{country_code[:2]}", exist_ok=True)
        processed_path = (
            f"countries/processed/{country_code[:2]}/{country_code}.geojson"
        )
    with open(processed_path, "w") as file:
        json.dump(data, file)
    return processed_path


def get_subdivisions(country_code) -> list:
    # Find the country by its ISO 3166-1 alpha-2 code
    country = pycountry.countries.get(alpha_2=country_code)
    if country:
        # Get all subdivisions for the country and keep only 1st level subs
        return [
            s.code
            for s in pycountry.subdivisions.get(country_code=country.alpha_2)
            if not s.parent_code
        ]
    else:
        print("Country code not found.")
        return []


def clip_to_boundary(
    train_lines_gdf: gpd.GeoDataFrame, state_boundary_geojson
) -> gpd.GeoDataFrame:
    if not state_boundary_geojson:
        return train_lines_gdf
    if not state_boundary_geojson["features"]:
        return train_lines_gdf
    state_gdf = gpd.GeoDataFrame.from_features(
        state_boundary_geojson["features"], crs=train_lines_gdf.crs
    )
    clipped_lines = gpd.clip(train_lines_gdf, state_gdf)
    return clipped_lines


def fetch_country_boundary(country_code, iso_code_level=1):
    query = f"""
    [out:json];
    relation["ISO3166-{iso_code_level}"="{country_code}"];
    (._; >;);
    out body;
    """
    url = "http://overpass-api.de/api/interpreter"
    response = requests.get(url, params={"data": query})
    if response.status_code == 200:
        osm_json = response.json()
        # Convert OSM JSON to GeoJSON using osm2geojson
        geojson = osm2geojson.json2geojson(
            osm_json, filter_used_refs=True, log_level="ERROR"
        )
        return geojson
    else:
        print("Error fetching data:", response.status_code)
        return None


def calculate_area(gdf):
    final_data: dict = {"type": "FeatureCollection", "features": []}
    # Transform to Web Mercator for accurate area calculations
    gdf_mercator = gdf.to_crs("EPSG:3857")
    # Compute the area for each geometry
    gdf_mercator["area_m2"] = gdf_mercator["geometry"].area
    # Filter out invalid areas
    gdf_mercator = gdf_mercator[gdf_mercator["area_m2"].notna()]
    # Transform back to WGS84
    gdf = gdf_mercator.to_crs("EPSG:4326")
    # Update the stripped_data with the valid features
    final_data["features"] = gdf.drop(columns=["geometry"]).to_dict("records")
    for idx, feature in enumerate(final_data["features"]):
        feature["geometry"] = mapping(gdf.iloc[idx].geometry)
        if "properties" not in feature or not isinstance(feature["properties"], dict):
            feature["properties"] = {}
        feature["properties"]["id"] = idx
        feature["properties"]["area_m2"] = gdf_mercator.iloc[idx]["area_m2"]

    # Compute the total area
    total_area_m2 = gdf_mercator["area_m2"].sum()
    final_data["total_area_m2"] = total_area_m2

    return final_data


def process(subdivision, is_country=False):
    start_time = time()

    # get data from file or overpass API
    step_time = time()
    data = fetch_railway_geometry(subdivision, is_country)
    print(
        f"({subdivision}) Fetched railway geometry in {time() - step_time:.2f} seconds."
    )

    if data == {}:
        return []

    # buffer the lines
    step_time = time()
    polygon_data = generate_polygons(data)
    print(
        f"({subdivision}) Buffered {len(polygon_data['features'])} in {time() - step_time:.2f} seconds."
    )

    # simplify polygons
    step_time = time()
    polygons = [shape(feature["geometry"]) for feature in polygon_data["features"]]
    polygons = [
        shape(shapely.simplify(feature, SIMPLIFY_TOLERANCE)) for feature in polygons
    ]
    print(
        f"({subdivision}) Simplified {len(polygons)} in {time() - step_time:.2f} seconds."
    )

    # generate cut lines
    step_time = time()
    cut_lines = generate_cut_lines(polygons)
    print(
        f"({subdivision}) Generated {len(cut_lines)} cut lines in {time() - step_time:.2f} seconds."
    )

    # partially merge overlapping polygons
    step_time = time()
    polygons = merge_overlapping_polygons(
        polygons, max_overlap_percentage=PRE_MERGE_PERCENTAGE, max_overlap_area=1000000
    )
    print(
        f"({subdivision}) Pre-merged {len(polygons)} in {time() - step_time:.2f} seconds."
    )

    # apply cuts
    step_time = time()
    cut_polygons = cut_polygons_with_lines(polygons, cut_lines)
    print(
        f"({subdivision}) Cut {len(cut_polygons)} in {time() - step_time:.2f} seconds."
    )

    # clip to (subdivision) boundary here
    step_time = time()
    sub_gdf = gpd.GeoDataFrame({"geometry": cut_polygons}, crs="EPSG:4326")
    # TODO check whether to_geo_dict() also works instead of to_json() -> json.loads()
    clipped_data = json.loads(
        clip_to_boundary(
            sub_gdf, fetch_country_boundary(subdivision, iso_code_level=2)
        ).to_json()
    )
    clipped_polygons = [
        shape(feature["geometry"]) for feature in clipped_data["features"]
    ]
    print(f"({subdivision}) Clipped in {time() - step_time:.2f} seconds.")

    # merge overlapping polygons
    step_time = time()
    merged_polygons = merge_overlapping_polygons(
        clipped_polygons, max_overlap_percentage=POST_MERGE_MAX_AREA
    )
    print(
        f"({subdivision}) Post-merged {len(merged_polygons)} in {time() - step_time:.2f} seconds."
    )

    # return only the features
    polys_gdf = gpd.GeoDataFrame({"geometry": merged_polygons}, crs="EPSG:4326")

    print(f"Processed {subdivision} in {time() - start_time:.2f} seconds!")
    features = json.loads(polys_gdf.to_json())["features"]
    return export(subdivision, features)


def fetch_railway_geometry(subdivision, is_country=False) -> dict:
    raw_data_path = f"countries/preprocessed/{subdivision[:2]}/{subdivision}.json"
    os.makedirs(f"countries/preprocessed/{subdivision[:2]}", exist_ok=True)
    if not os.path.isfile(raw_data_path):
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = f"""
                [out:json];
                area["ISO3166-{1 if is_country else 2}"="{subdivision}"]->.searchArea;
                (
                    way["railway"="rail"](area.searchArea);
                    way["railway"="narrow_gauge"](area.searchArea);
                    way["railway"="preserved"](area.searchArea);
                );
                out body;
                >;
                out skel qt;
                """

        response = requests.get(overpass_url, params={"data": overpass_query})
        try:
            data = response.json()
        except JSONDecodeError:
            return {}

        with open(raw_data_path, "w") as f:
            json.dump(data, f)
    else:
        with open(raw_data_path, "r") as f:
            data = json.load(f)
    return data


def generate_polygons(data) -> dict:
    def buffer_linestring(line_coords):
        line = LineString(line_coords)
        gdf = gpd.GeoDataFrame({"geometry": [line]}, crs="EPSG:4326")

        # Buffer the linestring and transform to Web Mercator for accurate distance calculations
        gdf = gdf.to_crs("EPSG:3857")
        gdf["geometry"] = gdf.buffer(RAIL_WIDTH_BUFFER_M)

        # Transform back to WGS84
        gdf = gdf.to_crs("EPSG:4326")

        return gdf.iloc[0].geometry

    nodes_dict = {
        node["id"]: (node["lon"], node["lat"])
        for node in data["elements"]
        if node["type"] == "node"
    }
    polygon_data = {"type": "FeatureCollection", "features": []}
    railway_sub_tags = [
        "abandoned",
        "disused",
        "razed",
        "construction",
        "proposed",
        "miniature",
        "loading_ramp",
        "traverser",
        "ferry",
    ]

    for element in data["elements"]:
        if (
            element["type"] == "way"
            and element["tags"]["railway"] not in railway_sub_tags
            and element["tags"].get("service") not in ["yard", "spur", "siding"]
            and element["tags"].get("usage") not in ["industrial", "military", "test"]
            and element["tags"].get("abandoned:railway")
            not in ["rail", "narrow_gauge", "tram", "yes"]
            and element["tags"].get("disused:railway")
            not in ["rail", "narrow_gauge", "tram", "yes"]
            # and element["tags"].get("railway:traffic_mode") not in ["freight", "military"]
        ):
            buffered_geometry = buffer_linestring(
                [(nodes_dict[node_id]) for node_id in element["nodes"]]
            )
            feature = {
                "type": "Feature",
                "id": element["id"],
                "properties": {},
                "geometry": shape(buffered_geometry).__geo_interface__,
            }
            polygon_data["features"].append(feature)

    return polygon_data


def generate_cut_lines(polygons: list) -> list:
    def angle_between(a, b, c):
        ba = np.array(a) - np.array(b)
        bc = np.array(c) - np.array(b)
        cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        cosine = np.clip(cosine, -1, 1)
        return np.degrees(np.arccos(cosine))

    def unit_vector(p0, p1):
        vec = np.array(p1) - np.array(p0)
        return vec / np.linalg.norm(vec)

    if not polygons:
        return []

    # Project polygons to EPSG:3857 (Web mercator, flat metric projection) which is used by web-based maps such as Google Maps, Mapbox etc
    # for correct angle/perpendicular math. As EPSG:4326/WGS84 is a geodesic system and EPSG:3857/Web Mercator is a flat metric projection, 
    # angles get distorted as latitude moves away from the equator. Projecting to Web Mercator helps avoid distortion.
    gdf = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:4326").to_crs("EPSG:3857")
    merged = gdf.union_all()

    outlines = []
    if isinstance(merged, MultiPolygon):
        for poly in merged.geoms:
            outlines.append(poly.exterior)
            outlines.extend(poly.interiors)
    else:
        outlines.append(merged.exterior)
        outlines.extend(merged.interiors)

    sharp_corners = []
    for outline in outlines:
        coords = list(outline.coords)
        for i in range(1, len(coords) - 1):
            a, b, c = coords[i - 1], coords[i], coords[i + 1]
            angle = angle_between(a, b, c)
            if angle < 90:
                sharp_corners.append((b, a, c))

    cut_lines: list[LineString] = []
    for corner, prev, nxt in sharp_corners:
        p_corner = np.array(corner)

        vec1 = unit_vector(prev, corner)
        vec2 = unit_vector(nxt, corner)

        perp1 = np.array([-vec1[1], vec1[0]])
        perp2 = np.array([-vec2[1], vec2[0]])

        vec_cut1 = unit_vector(corner, corner + perp1)
        dot1 = np.dot(vec_cut1, vec2)
        angle1 = np.degrees(np.arccos(np.clip(dot1, -1, 1)))
        if angle1 > 90:
            perp1 = -perp1

        vec_cut2 = unit_vector(corner, corner + perp2)
        dot2 = np.dot(vec_cut2, vec1)
        angle2 = np.degrees(np.arccos(np.clip(dot2, -1, 1)))
        if angle2 > 90:
            perp2 = -perp2

        # Extend lines by 200 meters. As Web mercator is a flat metric projection, this can just be expressed as 200.
        cut1_end = p_corner + perp1 * 200
        cut2_end = p_corner + perp2 * 200

        cut_lines.append(
            LineString([tuple(cut1_end), tuple(p_corner), tuple(cut2_end)])
        )

    # Project cut lines from EPSG:3857/Web Mercator back to EPSG:4326/WGS84.
    cut_gdf = gpd.GeoDataFrame(geometry=cut_lines, crs="EPSG:3857").to_crs("EPSG:4326")
    return list(cut_gdf.geometry)


def merge_overlapping_polygons(
    polygons: list, max_overlap_percentage: float = 0.9, max_overlap_area: float = 0.0
) -> list:
    """
    Groups and merges overlapping polygons.

    Args:
        polygons (list): List of shapely Polygon or MultiPolygon objects.
        max_overlap_percentage (float): Maximum tolerated percentage of overlap between two polygons.
        max_overlap_area (float): Maximum tolerated area of overlap between two polygons.

    Returns:
        list: List of merged shapely Polygon or MultiPolygon objects.
    """
    n = len(polygons)
    visited = [False] * n
    merged_groups = []

    for i in range(n):
        if visited[i]:
            continue

        group = [polygons[i]]
        visited[i] = True
        queue = [i]

        while queue:
            current = queue.pop(0)
            for j in range(n):
                if not visited[j] and polygons[current].intersects(polygons[j]):
                    intersect = polygons[current].intersection(polygons[j])
                    if (
                        intersect.area > max_overlap_area
                        or intersect.area
                        > min(polygons[current].area, polygons[j].area)
                        * max_overlap_percentage
                    ):
                        visited[j] = True
                        group.append(polygons[j])
                        queue.append(j)

        merged = unary_union(group)
        merged_groups.append(merged)

    return merged_groups


def cut_polygons_with_lines(polygons: list, lines: list[LineString]) -> list:
    """
    Iteratively cuts a list of polygons/multipolygons by a list of lines.

    Args:
        polygons (list): List of shapely Polygon or MultiPolygon objects.
        lines (list): List of shapely LineString objects.

    Returns:
        list: List of resulting polygons after all cuts.
    """
    current_polys = polygons[:]

    for line in lines:
        next_polys = []
        for poly in current_polys:
            try:
                result = split(poly, line)
                for geom in result.geoms:
                    if isinstance(geom, (Polygon, MultiPolygon)):
                        next_polys.append(geom)
            except Exception:
                # If splitting fails (e.g., no intersection), keep the original
                next_polys.append(poly)
        current_polys = next_polys

    return current_polys


if __name__ == "__main__":
    total_start = time()

    if len(sys.argv) < 2:
        print("Please provide a country's ISO code as a command-line argument.")
        sys.exit(1)

    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else NUM_CORES)

    print(
        f"Railway geometry processing for {sys.argv[1]} completed in {time() - total_start:.2f} seconds!"
    )
