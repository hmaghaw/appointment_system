#!/usr/bin/env bash
set -euo pipefail

# Load environment variables (must define S3_BUCKET, S3_PREFIX, DATA_DIR)
. /home/ec2-user/appointment_system/db_backup_restore/create_env_vars.sh

# Check if filename argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file_name.tar.gz>"
    exit 1
fi

BACKUP_FILE="$1"

# Validate the file exists in S3
if ! aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_FILE}" >/dev/null 2>&1; then
    echo "Error: Backup file '$BACKUP_FILE' not found in s3://${S3_BUCKET}/${S3_PREFIX}/"
    exit 1
fi

echo "Restoring ${BACKUP_FILE}"
cd ~/appointment_system/
docker-compose stop db

mkdir -p "$HOME/db_data_backup"
aws s3 cp "s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_FILE}" "$HOME/db_data_backup/"
aws s3 cp "s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_FILE}.sha256" "$HOME/db_data_backup/" 2>/dev/null || true

if [ -f "$HOME/db_data_backup/${BACKUP_FILE}.sha256" ]; then
    (cd "$HOME/db_data_backup" && sha256sum -c "${BACKUP_FILE}.sha256")
fi

sudo rm -rf "$DATA_DIR"
mkdir -p "$DATA_DIR"

if command -v pigz >/dev/null 2>&1; then
    pigz -dc "$HOME/db_data_backup/${BACKUP_FILE}" | sudo tar -x -C "$(dirname "$DATA_DIR")"
else
    gzip -dc "$HOME/db_data_backup/${BACKUP_FILE}" | sudo tar -x -C "$(dirname "$DATA_DIR")"
fi

sudo chown -R 999:999 "$DATA_DIR"
docker-compose start db
