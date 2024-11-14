# Import necessary QGIS and Python libraries
from qgis.core import QgsProject, QgsFeatureRequest, QgsExpression

# Load your master city layer (replace 'world_cities_3857' with the name of your layer)
master_layer = QgsProject.instance().mapLayersByName('cities')[0]

# Field names (adjust to match your actual field names)
country_field = 'FIPS_CNTRY'  # Country code
capital_field = 'capital'     # Indicator if city is capital (1 for capital)
type_field = 'type'           # Type of city ('inland' or 'coast')
population_field = 'pop'      # Population field for calculating closest city by population

# Create a dictionary to store one qualifying city per country to avoid duplicates
qualifying_cities = {}

# Loop through each unique country in the layer
countries = master_layer.uniqueValues(master_layer.fields().indexFromName(country_field))

for country_code in countries:
    print(f"Processing country: {country_code}")
    country_cities = master_layer.getFeatures(QgsFeatureRequest(QgsExpression(f'"{country_field}" = \'{country_code}\'')))

    # Find the capital city for this country
    capital_city = None
    for city in country_cities:
        if city[capital_field] == 1:
            capital_city = city
            break
    
    if not capital_city:
        print(f"No capital city found for country {country_code}")
        continue

    # Add the capital city to the qualifying cities dictionary
    qualifying_cities[country_code] = [capital_city]  # Add the capital as a list to allow adding the closest city later
    print(f"Capital city added: {capital_city['CITY_NAME']} with type {capital_city[type_field]}")

    # Determine the required city type (opposite of the capital's type)
    capital_city_type = capital_city[type_field]
    opposite_type = 'inland' if capital_city_type == 'coast' else 'coast'

    # Reset the country cities iterator to find cities of the opposite type
    country_cities = master_layer.getFeatures(QgsFeatureRequest(QgsExpression(f'"{country_field}" = \'{country_code}\'')))

    # Find the opposite-type city closest in population to the capital city
    closest_city = None
    smallest_pop_diff = float('inf')
    for city in country_cities:
        if city[type_field] == opposite_type and city != capital_city:
            # Ensure population values are integers for calculations
            capital_pop = capital_city[population_field]
            if isinstance(capital_pop, str):  # If population is a string, remove commas
                capital_pop = int(capital_pop.replace(',', ''))
            
            city_pop = city[population_field]
            if isinstance(city_pop, str):  # If population is a string, remove commas
                city_pop = int(city_pop.replace(',', ''))
            
            pop_diff = abs(city_pop - capital_pop)
            
            if pop_diff < smallest_pop_diff:
                smallest_pop_diff = pop_diff
                closest_city = city

    if closest_city:
        # Append the closest opposite-type city to the country's entry in the dictionary
        qualifying_cities[country_code].append(closest_city)
        print(f"Opposite-type city added: {closest_city['CITY_NAME']} with type {closest_city[type_field]}")

# Optional: Create a new layer to store qualifying cities
qualifying_layer = QgsVectorLayer("Point?crs=EPSG:4326", "Qualifying Cities", "memory")
qualifying_layer_data = qualifying_layer.dataProvider()
qualifying_layer_data.addAttributes(master_layer.fields())
qualifying_layer.updateFields()

# Flatten the dictionary into a list of features to add to the layer
features_to_add = [city for cities in qualifying_cities.values() for city in cities]
qualifying_layer_data.addFeatures(features_to_add)
QgsProject.instance().addMapLayer(qualifying_layer)

print("Qualifying cities layer created.")
