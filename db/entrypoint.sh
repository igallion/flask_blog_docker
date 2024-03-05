#!/bin/sh

export MONGO_INITDB_ROOT_USERNAME=$(cat /run/secrets/mongo_root_username)
export MONGO_INITDB_ROOT_PASSWORD=$(cat /run/secrets/mongo_root_password)

# Then, execute the main process (for example, start your application)
exec "$@"