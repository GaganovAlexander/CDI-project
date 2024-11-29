#!/bin/bash

ask_for_value() {
  local prompt=$1
  local default_value=$2
  echo "$prompt (default: $default_value): " > /dev/tty
  read input
  echo ${input:-$default_value}
}

ELASTIC_PORT=$(ask_for_value "Enter the port for Elasticsearch" "9200")
REDIS_PORT=$(ask_for_value "Enter the port for Redis" "6379")
APP_PORT=$(ask_for_value "Enter the port for the Flask application" "5000")

echo "Received values:"
echo "Elasticsearch port: $ELASTIC_PORT"
echo "Redis port: $REDIS_PORT"
echo "App port: $APP_PORT"

echo "Enter the Elasticsearch superuser password: "
read -s ELASTIC_PASSWORD
echo

echo "Enter full path to directory(on host) where pdf files will be stored: "
read PDFS_DIR
echo

cat > .env <<EOL
APP_PORT=$APP_PORT

ELASTIC_URL=http://elasticsearch:$ELASTIC_PORT
ELASTIC_USER=elastic
ELASTIC_PASSWORD=$ELASTIC_PASSWORD
ELASTIC_PORT=$ELASTIC_PORT

REDIS_PORT=$REDIS_PORT

PDFS_DIR=$PDFS_DIR
EOL

echo ".env file has been created."

export $(grep -v '^#' .env | xargs)

echo "Environment variables have been set."

echo "Now you can run 'docker-compose up -d' to start the services."
