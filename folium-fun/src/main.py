import folium

# Create a Map instance
m = folium.Map(location=[45.5236, -122.6750], zoom_start=13)

# Add a marker to the map
folium.Marker(
    location=[45.5236, -122.6750],
    popup="The marker's location",
    icon=folium.Icon(icon="cloud"),
).add_to(m)

# Save the map to an HTML file
m.save("map.html")