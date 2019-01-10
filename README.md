# Nimos' Intel Tool

Nimos' Intel Tool is a web application that parses DScans and local scans from the game Eve Online. 


## Installation
1. Clone this repository
2. Edit `dscan/settings.py` to your liking
3. Get the EVE Static Data Export (SDE) from https://developers.eveonline.com/resource/resources
4. Extract `groupIDs.yaml` and `typeIDs.yaml` from the SDE into eve_data
5. Run `python manage.py import_types`
