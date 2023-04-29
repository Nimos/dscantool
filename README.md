# Nimos' Intel Tool

Nimos' Intel Tool is a web application that parses DScans and local scans from the game Eve Online.
I made it because my previous favorite Intel Tool dscan.me shut down and I wanted another one with a dark theme.

## Standalone installation

(I have not tested this method)

1. Clone this repository
2. Install requirements with `pip install -r requirements.txt` or from another source of your liking
3. Edit `dscantool/settings.py` to your liking
4. Install database with `python manage.py migrate`
5. Generate static files `python manage.py collectstatic --noinput`

### Optional: Import Type information from SDE

Note: Nimos' Intel Tool pulls all missing type information from ESI when needed. When starting out with an empty cache that can make the first scans take a couple of seconds to parse, but once a ship type is cached it won't be requested again. You can import all ship type information from SDE to "seed" the cache, but doing so is optional and the script is no longer maintained. Use at your own discretion or feel free to import the SDE another way.

1. Get the EVE Static Data Export (SDE) from https://developers.eveonline.com/resource/resources
2. Extract `groupIDs.yaml` and `typeIDs.yaml` from the SDE into `eve_data`
3. Run `python manage.py import_sde`

## Docker installation

### Environment Variables

| Variable            | Default                                            | Dscription |
|---------------------|----------------------------------------------------|------------|
|`DSCAN_SECRET_KEY`   |`&f8lk5k-b$^)-sdfij8gu9df7g9aa2zagdfh8iooijioukhrs_`|A secret key for a particular Django installation.|
|`DSCAN_ALLOWED_HOST` |`dscan.nimos.ws`                                    |String representing the host/domain name that this Django site can serve.|
|`DSCAN_DB_ENGINE`    |`django.db.backends.postgresql`                     |The database backend to use. The built-in database backends are: `django.db.backends.postgresql`, `django.db.backends.mysql`, `django.db.backends.sqlite3`, `django.db.backends.oracle`|
|`DSCAN_DB_NAME`      |`dscantool`                                         |The name of the database to use.|
|`DSCAN_DB_USER`      |`dscantool`                                         |The username to use when connecting to the database.|
|`DSCAN_DB_PASSWORD`  |`dscantool`                                         |The password to use when connecting to the database.|
|`DSCAN_DB_HOST`      |`127.0.0.1`                                         |Which host to use when connecting to the database.|
|`DSCAN_DB_PORT`      |`5432`                                              |The port to use when connecting to the database.|
|`DSCAN_LANGUAGE_CODE`|`en-us`                                             |A string representing the language code for this installation.|
|`DSCAN_STATIC_URL`   |`/static/`                                          |URL to use when referring to static files located in `DSCAN_STATIC_ROOT`.|
|`DSCAN_STATIC_ROOT`  |`/dscantool/static/`                                |The absolute path to the directory where collectstatic will collect static files for deployment.|

## Notes

This is just a little 2-day project, so don't expect the sleekest code.

This tool relies heavily on caching. The first few scans will be slow until the database has seen most ship types and corporations, after a couple of scans performance should increase significantly. The up-side is that you never have to update the static data like you have to for many other EVE tools.

This tool has been tested with MySQL and SQLite. Feel free to use other database backends, but they might require minor fixes. When using MySQL, make sure your tables (specifically the `dscan_scan` and `esi_invtype`) use the 'utf8mb4' encoding. Otherwise it will error out trying to save certain characters.
