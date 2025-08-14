#!/usr/bin/env bash
set -euo pipefail

# ===== CONFIG =====
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # repo root
DATA_DIR="$PROJECT_DIR/mysql_data"                            # mapped /var/lib/mysql
BACKUP_DIR="$PROJECT_DIR/backups"                             # local backup folder
DATE_STR="$(date +%F_%H%M%S)"
ARCHIVE_NAME="mysql_data_${DATE_STR}.tar.gz"
ARCHIVE_PATH="$BACKUP_DIR/$ARCHIVE_NAME"

# S3
S3_BUCKET="your-bucket-name"
S3_PREFIX="mysql-backups"          # folder inside the bucket
S3_URI="s3://${S3_BUCKET}/${S3_PREFIX}/${ARCHIVE_NAME}"

# Optional: AWS KMS key (uncomment to use KMS instead of AES256)
# SSE_ARGS=(--sse "aws:kms" --sse-kms-key-id "arn:aws:kms:ca-central-1:123456789012:key/your-key-id")
SSE_ARGS=(--sse "AES256")

# How many local backups to keep
KEEP_LOCAL=7

# ===== WORK =====
mkdir -p "$BACKUP_DIR"

echo "[1/6] Stopping DB container..."
docker-compose stop db

echo "[2/6] Creating archive..."
tar -czf "$ARCHIVE_PATH" -C "$PROJECT_DIR" mysql_data

echo "[3/6] Starting DB container..."
docker-compose start db

echo "[4/6] Calculating checksum..."
sha256sum "$ARCHIVE_PATH" > "${ARCHIVE_PATH}.sha256"

echo "[5/6] Uploading to S3: $S3_URI"
aws s3 cp "$ARCHIVE_PATH" "$S3_URI" "${SSE_ARGS[@]}" --storage-class STANDARD_IA --no-progress
aws s3 cp "${ARCHIVE_PATH}.sha256" "${S3_URI}.sha256" "${SSE_ARGS[@]}" --storage-class STANDARD_IA --no-progress

echo "[6/6] Local rotation (keep last $KEEP_LOCAL)..."
ls -1t "$BACKUP_DIR"/mysql_data_*.tar.gz | tail -n +$((KEEP_LOCAL+1)) | xargs -r rm -f
ls -1t "$BACKUP_DIR"/mysql_data_*.tar.gz.sha256 | tail -n +$((KEEP_LOCAL+1)) | xargs -r rm -f

echo "Done."
