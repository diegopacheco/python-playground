capitals = {
    "Brazil": "Brazilia",
    "Usa": "DC",
    "France": "Paris",
    "Germany": "Berlin",
    "Italy": "Rome",
    "Argentina": "Buenos Aires",
}
print(capitals)

print(capitals.get("Brazil"))
print(capitals.get("Uruguay", "Montevideo"))
print(capitals["Usa"])
