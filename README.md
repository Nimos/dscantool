# Nimos' Intel Tool

Nimos' Intel Tool is a web application that parses DScans and local scans from the game Eve Online.  
I made it because my previous favorite Intel Tool dscan.me shut down and I wanted another one with a dark theme.


## Installation
1. Clone this repository
2. Install requirements with `pip3 install -r requirements.txt` or from another source of your liking
3. Edit `dscan/settings.py` to your liking
4. Install database with `python3 manage.py migrate` 

## Optional: Import Type information from SDE
Note: Nimos' Intel Tool pulls all missing type information from ESI when needed. When starting out with an empty cache that can make the first scans take a couple of seconds to parse, but once a ship type is cached it won't be requested again. You can import all ship type information from SDE to "seed" the cache, but doing so is optional and the script is no longer maintained.

1. Get the EVE Static Data Export (SDE) from https://developers.eveonline.com/resource/resources
2. Extract `groupIDs.yaml` and `typeIDs.yaml` from the SDE into eve_data
3. Run `python3 manage.py import_types`


## Notes
This is just a little 2-day project, so don't expect the sleekest code.

This tool relies heavily on caching. The first few scans will be slow until the database has seen most ship types and corporations, after a couple of scans performance should increase significantly. The up-side is that you never have to update the static data like you have to for many other EVE tools.