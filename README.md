# Nimos' Intel Tool

Nimos' Intel Tool is a web application that parses DScans and local scans from the game Eve Online.  
I made it because my previous favorite Intel Tool dscan.me shut down and I wanted another one with a dark theme.


## Installation
1. Clone this repository
2. Install requirements with `pip3 install -r requirements.txt` or from another source of your liking
3. Edit `dscan/settings.py` to your liking
4. Install database with `python3 manage.py migrate` 
4. Get the EVE Static Data Export (SDE) from https://developers.eveonline.com/resource/resources
5. Extract `groupIDs.yaml` and `typeIDs.yaml` from the SDE into eve_data
6. Run `python3 manage.py import_types`


## Notes
It's just a little 2-day project, so don't expect the sleekest code.