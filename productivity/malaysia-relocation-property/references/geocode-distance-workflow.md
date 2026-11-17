# Geocoding and drive-time workflow for "what is near X"

Use when the user asks where a project/landmark is, or wants options near an anchor address. Built for hosts where Google Maps is not callable and where geocoding APIs rate-limit server traffic.

## Steps

1. **Get a postal address first.** A project name alone rarely geocodes. Mine the document the user sent (invoice, listing, title) and/or property-portal search snippets for the street address, postcode and township, then geocode the street.
2. **Geocode** with photon (no key, tolerant of server traffic):

```python
import json, urllib.parse, urllib.request
UA = "Mozilla/5.0 (compatible; HermesAgent/1.0)"
def photon(q):
    u = "https://photon.komoot.io/api/?" + urllib.parse.urlencode({"q": q, "limit": 5, "lang": "en"})
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as f:
        d = json.load(f)
    return [(p["properties"].get("name"), p["geometry"]["coordinates"][1],
             p["geometry"]["coordinates"][0], p["properties"].get("city"),
             p["properties"].get("postcode")) for p in d["features"]]
```

3. **Distances two ways**: haversine for straight-line sanity, OSRM for real drive time:

```python
# OSRM: coordinates are LON,LAT — reversing them yields a wrong or empty route
url = f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
r = json.load(urllib.request.urlopen(url))["routes"][0]
print(r["distance"] / 1000, "km", r["duration"] / 60, "min")
```

4. **Save results to a JSON file** as you go, so a follow-up question ("and the schools?") can be answered from the cache instead of re-geocoding.
5. **Report with honesty**: road-level geocoding is ±300–500 m. Give the coordinates, a Google Maps search link built from the project name + address, a coordinate link, and say the exact lot/unit is confirmed from the title or plot number (PTO / H.S.(D)) or from the developer.

## Pitfalls

- **Fallback ladder for geocoding:** if Nominatim returns 403 for your host, do not retry it repeatedly — switch to photon; if Overpass returns 406, request points of interest with an explicit `Accept` header or skip them. A supermarket, hospital or school near the street is usually enough to anchor the answer.
- Never let a landmark's coordinates stand in for the project's coordinates without saying so — name which point you measured from.
- Distances the user cares about are **driving** minutes, not straight-line km; give both, but lead with driving.
- Batch each sub-procedure (geocode several names, one route matrix) into a single script, then print a compact "name -> km to anchor A / km to anchor B" table rather than one call per landmark.
