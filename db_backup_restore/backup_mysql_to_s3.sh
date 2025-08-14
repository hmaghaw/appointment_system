#!/usr/bin/env bash
set -euo pipefail
# Set Env Vars
. /home/ec2-user/appointment_system/db_backup_restore/create_env_vars.sh

# Create backup folder if it doesn't exist
mkdir -p "$BACKUP_DIR"

cd ~/appointment_system/
echo "[1/6] Stopping DB container..."
docker-compose stop db

echo "[2/6] Creating archive from $DATA_DIR..."
sudo tar -cf - -C "$(dirname "$DATA_DIR")" "$(basename "$DATA_DIR")" | pigz -1 > "${BACKUP_DIR}/${ARCHIVE_NAME}"

echo "[3/6] Starting DB container..."
docker-compose start db

echo "[4/6] Calculating checksum..."
sha256sum ${ARCHIVE_PATH} > ${ARCHIVE_PATH}.sha256

echo "[5/6] Uploading to S3: $S3_URI"

aws s3 cp ${ARCHIVE_PATH} ${S3_URI} --sse "AES256" --storage-class STANDARD_IA --no-progress
aws s3 cp "${ARCHIVE_PATH}.sha256" "${S3_URI}.sha256" "${SSE_ARGS[@]}" --storage-class STANDARD_IA --no-progress

echo "[6/6] Local rotation (keep last $KEEP_LOCAL)..."
ls -1t "$BACKUP_DIR"/mysql_data_*.tar.gz | tail -n +$((KEEP_LOCAL+1)) | xargs -r rm -f
ls -1t "$BACKUP_DIR"/mysql_data_*.tar.gz.sha256 | tail -n +$((KEEP_LOCAL+1)) | xargs -r rm -f

echo "Backup complete."