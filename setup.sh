#!/bin/bash

ask_for_port() {
  local prompt=$1
  local default_value=$2
  local value

  while true; do
    echo "$prompt (default: $default_value): " > /dev/tty
    read value
    value=${value:-$default_value}

    if [[ "$value" =~ ^[1-9][0-9]*$ ]]; then
      echo "$value"
      break
    fi
    echo "Invalid input. Please enter a valid number (port must be positive integer number and cannot start with 0)." > /dev/tty
  done
}

ELASTIC_PORT=$(ask_for_port "Enter the port for Elasticsearch" "9200")
REDIS_PORT=$(ask_for_port "Enter the port for Redis" "6379")
APP_PORT=$(ask_for_port "Enter the port for the Flask application" "5000")

echo "Received values:"
echo "Elasticsearch port: $ELASTIC_PORT"
echo "Redis port: $REDIS_PORT"
echo "App port: $APP_PORT"

while true; do
  echo "Enter the Elasticsearch superuser password: "
  read -s ELASTIC_PASSWORD
  echo

  if [[ ${#ELASTIC_PASSWORD} -lt 8 ]]; then
    echo "Password must be at least 8 characters long. Please try again."
    continue
  fi

  echo "Confirm the password: "
  read -s ELASTIC_PASSWORD_CONFIRM
  echo

  if [[ "$ELASTIC_PASSWORD" != "$ELASTIC_PASSWORD_CONFIRM" ]]; then
    echo "Passwords do not match. Please try again."
  else
    break
  fi
done

cat > .env <<EOL
APP_PORT=$APP_PORT

ELASTIC_URL=http://elasticsearch:$ELASTIC_PORT
ELASTIC_USER=elastic
ELASTIC_PASSWORD=$ELASTIC_PASSWORD
ELASTIC_PORT=$ELASTIC_PORT

REDIS_PORT=$REDIS_PORT

PDFS_DIR=$(pwd)/pdfs
EOL

echo ".env file has been created."