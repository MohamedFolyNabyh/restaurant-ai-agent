import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

OVERPASS_URL = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"

HEADERS = {
    "User-Agent": "RestaurantAIAgent/1.0"
}


city_cache = {}


def get_city_coordinates(city: str):

    if city in city_cache:
        return city_cache[city]

    params = {
        "q": city,
        "format": "jsonv2",
        "limit": 1,
        "countrycodes":"eg"  # Limit search to Egypt
    }

    response = requests.get(
        NOMINATIM_URL,
        params=params,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()

    locations = response.json()

    if not locations:
        return {
            "error": f"Could not find city: {city}"
        }

    latitude = float(locations[0]["lat"])
    longitude = float(locations[0]["lon"])

    coordinates = {
        "latitude": latitude,
        "longitude": longitude
    }

    city_cache[city] = coordinates

    return coordinates


def search_restaurants(city: str):

    coordinates = get_city_coordinates(city)

    if "error" in coordinates:
        return coordinates

    latitude = coordinates["latitude"]
    longitude = coordinates["longitude"]

    query = f"""
    [out:json][timeout:50];

    (
        node["amenity"="restaurant"](around:10000,{latitude},{longitude});
        way["amenity"="restaurant"](around:10000,{latitude},{longitude});
        relation["amenity"="restaurant"](around:10000,{latitude},{longitude});
    );

    out center tags;
    """

    response = requests.post(
        OVERPASS_URL,
        data=query,
        headers=HEADERS,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    restaurants = []

    for element in data.get("elements", []):

        tags = element.get("tags", {})

        name = tags.get("name")

        if not name:
            continue

        restaurants.append({
            "name": name,
            "cuisine": tags.get("cuisine"),
            "phone": tags.get("phone"),
            "website": tags.get("website")
        })

    return restaurants[:20]


def search_restaurants_by_cuisine(city: str, cuisine: str):

    coordinates = get_city_coordinates(city)

    if "error" in coordinates:
        return coordinates

    latitude = coordinates["latitude"]
    longitude = coordinates["longitude"]

    query = f"""
    [out:json][timeout:50];

    (
        node["amenity"="restaurant"]["cuisine"~"{cuisine}", i]
            (around:10000,{latitude},{longitude});

        way["amenity"="restaurant"]["cuisine"~"{cuisine}", i]
            (around:10000,{latitude},{longitude});

        relation["amenity"="restaurant"]["cuisine"~"{cuisine}", i]
            (around:10000,{latitude},{longitude});
    );

    out center tags;
    """

    response = requests.post(
        OVERPASS_URL,
        data=query,
        headers=HEADERS,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    restaurants = []

    for element in data.get("elements", []):

        tags = element.get("tags", {})

        name = tags.get("name")

        if not name:
            continue

        restaurants.append({
            "name": name,
            "cuisine": tags.get("cuisine"),
            "phone": tags.get("phone"),
            "website": tags.get("website")
        })

    return restaurants[:20]


def get_restaurant_details(restaurant_name: str, city: str):

    coordinates = get_city_coordinates(city)

    if "error" in coordinates:
        return coordinates

    latitude = coordinates["latitude"]
    longitude = coordinates["longitude"]

    query = f"""
    [out:json][timeout:50];

    (
        node["amenity"="restaurant"]["name"="{restaurant_name}"]
            (around:10000,{latitude},{longitude});

        way["amenity"="restaurant"]["name"="{restaurant_name}"]
            (around:10000,{latitude},{longitude});

        relation["amenity"="restaurant"]["name"="{restaurant_name}"]
            (around:10000,{latitude},{longitude});
    );

    out center tags;
    """

    response = requests.post(
        OVERPASS_URL,
        data=query,
        headers=HEADERS,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    elements = data.get("elements", [])

    if not elements:
        return {
            "error": (
                f"No details found for restaurant "
                f"'{restaurant_name}' in city '{city}'."
            )
        }

    element = elements[0]

    tags = element.get("tags", {})

    return {
        "name": tags.get("name"),
        "cuisine": tags.get("cuisine"),
        "phone": tags.get("phone"),
        "website": tags.get("website"),
        "address": {
            "street": tags.get("addr:street"),
            "housenumber": tags.get("addr:housenumber"),
            "postcode": tags.get("addr:postcode"),
            "city": tags.get("addr:city")
        }
    }