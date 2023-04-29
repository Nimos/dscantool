### BUILDER

FROM python:3.7-alpine as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/main

COPY ./requirements.txt .

RUN set -eux; \
    apk add \
        gcc \
        libc-dev \
        libffi-dev \
        postgresql-dev \
        python3-dev \
        musl-dev \
    ; \
    pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/main/wheels -r requirements.txt

### FINAL

FROM python:3.7-alpine

ENV DSCAN_HOME_DIR ${DSCAN_HOME_DIR:-/dscantool}
ENV DSCAN_WORK_DIR $DSCAN_HOME_DIR/app
ENV DSCAN_STATIC_DIR $DSCAN_HOME_DIR/static
ENV DSCAN_GROUP ${DSCAN_GROUP:-dscantool}
ENV DSCAN_GID ${DSCAN_GID:-10000}
ENV DSCAN_USER ${DSCAN_USER:-dscantool}
ENV DSCAN_UID ${DSCAN_UID:-10000}
ENV DSCAN_PORT ${DSCAN_PORT:-8000}
ENV GOSU_VERSION 1.16

WORKDIR $DSCAN_WORK_DIR

COPY --from=builder /usr/src/main/wheels /wheels
COPY --from=builder /usr/src/main/requirements.txt .
COPY . $DSCAN_WORK_DIR

# Install gosu
RUN set -eux; \
	\
	apk add --no-cache --virtual .gosu-deps \
		ca-certificates \
		dpkg \
		gnupg \
	; \
	\
	dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')"; \
	wget -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch"; \
	wget -O /usr/local/bin/gosu.asc "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch.asc"; \
	\
# verify the signature
	export GNUPGHOME="$(mktemp -d)"; \
	gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4; \
	gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu; \
	gpgconf --kill all; \
	rm -rf "$GNUPGHOME" /usr/local/bin/gosu.asc; \
	\
# clean up fetch dependencies
	apk del --no-network .gosu-deps; \
	\
	chmod +x /usr/local/bin/gosu; \
# verify that the binary works
	gosu --version; \
	gosu nobody true

# Install dscantool
RUN \
    set -eux; \
    mkdir -p $DSCAN_WORK_DIR; \
    mkdir -p $DSCAN_STATIC_DIR; \
    addgroup -g $DSCAN_GID $DSCAN_GROUP; \
    adduser -u $DSCAN_UID -h $DSCAN_HOME_DIR -G $DSCAN_GROUP -D $DSCAN_USER; \
    apk add libpq tini; \
    pip install --no-cache /wheels/*; \
    chmod +x $DSCAN_WORK_DIR/run.sh; \
    chown -R $DSCAN_USER:$DSCAN_GROUP $DSCAN_HOME_DIR

# Get the EVE Static Data Export (SDE)
RUN \
    set -eux; \
    wget https://eve-static-data-export.s3-eu-west-1.amazonaws.com/tranquility/sde.zip; \
    unzip sde.zip; \
    for f in `find sde -iname "groupIDs.yaml"`; do cp $f ./eve_data/; done; \
    for f in `find sde -iname "typeIDs.yaml"`; do cp $f ./eve_data/; done; \
    rm -rf sde*

EXPOSE $DSCAN_PORT
VOLUME $DSCAN_STATIC_DIR
ENTRYPOINT ["tini", "--"]

CMD ["./run.sh"]
