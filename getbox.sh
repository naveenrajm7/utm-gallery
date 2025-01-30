#!/bin/sh
# shellcheck shell=dash

# This script downloads and installs a VM box from the gallery.
# It takes arguments: box_name (required), box_version (optional), box_arch (optional).

set -eu

# Function to display usage
usage() {
    cat <<EOF
Usage: $0 <box_name> [box_version] [box_arch]

Arguments:
  box_name      Name of the box (required)
  box_version   Version of the box (optional, defaults to latest)
  box_arch      Architecture of the box (optional, defaults to arm)
EOF
    exit 1
}

# Function to check if a command exists
need_cmd() {
    if ! command -v "$1" > /dev/null 2>&1; then
        err "Error: '$1' command not found."
    fi
}

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $*"
}

# Function to handle errors
err() {
    log "$1" >&2
    exit 1
}

# Function to fetch the latest version if not provided
fetch_latest_version() {
    local box_name=$1
    local versions_api_url="https://api.cloud.hashicorp.com/vagrant/2022-09-30/registry/utm/box/$box_name/versions"
    local response
    response=$(curl -sSf -w "%{http_code}" "$versions_api_url")
    local http_code=${response: -3}
    if [ "$http_code" -ne 200 ]; then
        err "Failed to fetch the latest version. HTTP status code: $http_code"
    fi
    RETVAL=$(echo "${response%$http_code}" | grep -o '"name":"[^"]*' | grep -o '[^"]*$' | head -n 1)
}

# Function to fetch download details
fetch_download_details() {
    local api_url=$1
    local response
    response=$(curl -sSf -w "%{http_code}" "$api_url")
    local http_code=${response: -3}
    if [ "$http_code" -ne 200 ]; then
        err "Failed to fetch download details. HTTP status code: $http_code"
    fi
    RETVAL="${response%$http_code}"
}

# Function to verify checksum
verify_checksum() {
    local checksum=$1
    local file=$2
    local checksum_type=$3

    if [ "$checksum_type" = "NONE" ]; then
        log "Checksum verification skipped as checksum type is NONE"
        return
    fi

    case "$checksum_type" in
      SHA1)
          checksum_type=1
          ;;
      SHA256)
          checksum_type=256
          ;;
      SHA384)
          checksum_type=384
          ;;          
      SHA512)
          checksum_type=512
          ;;
      *)
          err "Unsupported checksum type: $checksum_type"
          ;;
    esac

    echo "$checksum  $file" | shasum -a "$checksum_type" -c -
}

# Main script
main() {
    if [ $# -lt 1 ]; then
        usage
    fi

    local box_name=$1
    local box_version=${2:-}
    local box_arch=${3:-arm64}

    need_cmd curl
    need_cmd tar
    need_cmd osascript

    log "Starting the download process for box: $box_name, version: ${box_version:-latest}, architecture: $box_arch"

    if [ -z "$box_version" ]; then
        log "Fetching the latest version for box: $box_name"
        fetch_latest_version "$box_name" || return 1
        box_version="$RETVAL"
        log "Latest version for box $box_name is $box_version"
    fi

    local api_url="https://api.cloud.hashicorp.com/vagrant/2022-09-30/registry/utm/box/$box_name/version/$box_version/provider/utm/architecture/$box_arch/download"
    log "Fetching download details from API: $api_url"
    fetch_download_details "$api_url" || return 1
    local response="$RETVAL"
    local download_url=$(echo "$response" | grep -o '"url":"[^"]*' | grep -o '[^"]*$')
    local checksum=$(echo "$response" | grep -o '"checksum":"[^"]*' | grep -o '[^"]*$')
    local checksum_type=$(echo "$response" | grep -o '"checksum_type":"[^"]*' | grep -o '[^"]*$')

    log "Download URL: $download_url"
    log "Checksum: $checksum"
    log "Checksum Type: $checksum_type"

    local box_file="${box_name}_${box_version}_${box_arch}.box"
    log "Downloading the box file to $box_file"
    curl -L -o "$box_file" "$download_url"

    log "Verifying checksum"
    verify_checksum "$checksum" "$box_file" "$checksum_type"

    local temp_dir
    temp_dir=$(mktemp -d)
    log "Extracting the box file to $temp_dir"
    tar -xvf "$box_file" -C "$temp_dir"

    log "Finding .utm folder"
    local utm_folder
    utm_folder=$(find "$temp_dir" -type d -name "*.utm" | head -n 1)

    if [ -z "$utm_folder" ]; then
        err "No .utm folder found in the extracted files."
    fi

    log "Importing the VM to UTM"
    osascript -e "tell application \"UTM\" to import new virtual machine from POSIX file \"$utm_folder\""

    log "Cleaning up"
    rm "$box_file"
    rm -rf "$temp_dir"

    log "Download and installation process completed successfully"
}

main "$@"