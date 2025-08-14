#!/usr/bin/env bash
set -euo pipefail
. /home/ec2-user/appointment_system/db_backup_restore/create_env_vars.sh
# find latest .tar.gz in S3
LATEST=$(aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" \
  | awk '/\.tar\.gz$/ {print $4,$1,$2}' \
  | sort -k2,2 -k3,3 \
  | tail -n1 \
  | awk '{print $1}')

[ -z "$LATEST" ] && { echo "No .tar.gz backups found in s3://${S3_BUCKET}/${S3_PREFIX}/"; exit 1; }

echo "Restoring $LATEST"
cd ~/appointment_system/
docker-compose stop db

mkdir -p "$HOME/db_data_backup"
aws s3 cp "s3://${S3_BUCKET}/${S3_PREFIX}/${LATEST}" "$HOME/db_data_backup/"
aws s3 cp "s3://${S3_BUCKET}/${S3_PREFIX}/${LATEST}.sha256" "$HOME/db_data_backup/" 2>/dev/null || true

if [ -f "$HOME/db_data_backup/${LATEST}.sha256" ]; then
  (cd "$HOME/db_data_backup" && sha256sum -c "${LATEST}.sha256")
fi

sudo rm -rf "$DATA_DIR"
mkdir -p "$DATA_DIR"

if command -v pigz >/dev/null 2>&1; then
  pigz -dc "$HOME/db_data_backup/${LATEST}" | sudo tar -x -C "$(dirname "$DATA_DIR")"
else
  gzip -dc "$HOME/db_data_backup/${LATEST}" | sudo tar -x -C "$(dirname "$DATA_DIR")"
fi

sudo chown -R 999:999 "$DATA_DIR"
docker-compose start db
