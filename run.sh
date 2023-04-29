#!/bin/sh -eu

DSCAN_USER=${DSCAN_USER:-dscantool}
DSCAN_PORT=${DSCAN_PORT:-8000}
DSCAN_DB_HOST=${DSCAN_DB_HOST:-127.0.0.1}
DSCAN_DB_PORT=${DSCAN_DB_PORT:-5432}

if [ -z "$DSCAN_DB_HOST" ]; then
    echo "Error: DSCAN_DB_HOST is not set."
    exit 1
fi

if [ -z "$DSCAN_DB_PORT" ]; then
    echo "Error: DSCAN_DB_PORT is not set."
    exit 1
fi

echo "Info: Waiting for postgresql..."
while ! nc -z $DSCAN_DB_HOST $DSCAN_DB_PORT; do
    echo "Info: waiting."
    sleep 0.1
done
echo "Info: Postgresql started."

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py import_sde &
gosu $DSCAN_USER python manage.py runserver 0.0.0.0:$DSCAN_PORT
