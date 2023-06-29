#!/bin/sh
set -e

if [ -f /app/tmp/pids/server.pid ]; then
  rm /app/tmp/pids/server.pid
fi

# Get current state of database.
db_version=$(rake db:version)
db_status=$?

echo "DB Version: ${db_version}"
# Provision Database.
if [ "$db_status" != "0" ]; then
  echo "Creating database..."
  rake db:create
  echo "Migrating database..."
  rake db:migrate
elif [ "$db_version" = "Current version: 0" ]; then
  echo "Migrating database..."
  rake db:migrate
else
  echo "Migrating database..."
  (rake db:migrate:status | grep "^\s*down") && rake db:migrate || echo "No pending migrations found!"
fi

rails s -p 80 -b '0.0.0.0'
