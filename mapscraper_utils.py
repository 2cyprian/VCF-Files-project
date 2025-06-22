import requests
import urllib.parse

def scrape_osm(location, category, subcategory):
    # Build Overpass QL query for OSM
    # This is a simple example; you may want to refine tags for real use
    query = f"[out:json][timeout:25];area[name='{location}'];(node[amenity='{subcategory}'](area);way[amenity='{subcategory}'](area);relation[amenity='{subcategory}'](area););out center;"
    url = f"https://overpass-api.de/api/interpreter?data={urllib.parse.quote(query)}"
    resp = requests.get(url)
    data = resp.json()
    results = []
    for el in data.get('elements', []):
        tags = el.get('tags', {})
        results.append({
            'name': tags.get('name', ''),
            'phone': tags.get('phone', ''),
            'address': tags.get('addr:full', ''),
            'website': tags.get('website', ''),
            'lat': el.get('lat', el.get('center', {}).get('lat', '')),
            'lon': el.get('lon', el.get('center', {}).get('lon', '')),
        })
    return results

def scrape_google_maps(location, category, subcategory, serpapi_key):
    # Use SerpAPI for Google Maps scraping
    params = {
        'engine': 'google_maps',
        'q': f"{subcategory} {category} in {location}",
        'type': 'search',
        'api_key': serpapi_key
    }
    url = 'https://serpapi.com/search'
    resp = requests.get(url, params=params)
    data = resp.json()
    results = []
    for place in data.get('local_results', []):
        results.append({
            'name': place.get('title', ''),
            'phone': place.get('phone', ''),
            'address': place.get('address', ''),
            'website': place.get('website', ''),
            'lat': place.get('gps_coordinates', {}).get('latitude', ''),
            'lon': place.get('gps_coordinates', {}).get('longitude', ''),
        })
    return results
