#!/usr/bin/env bash
set -euo pipefail

# ===== CONFIG =====
DATA_DIR="$HOME/db_data"                                      # mapped /var/lib/mysql
BACKUP_DIR="$HOME/db_data_backup"                             # local backup folder
DATE_STR="$(date +%F_%H%M%S)"
ARCHIVE_NAME="mysql_data_${DATE_STR}.tar.gz"
ARCHIVE_PATH="$BACKUP_DIR/$ARCHIVE_NAME"

# S3
S3_BUCKET="polydial"
S3_PREFIX="mysql-backups"          # folder inside the bucket
S3_URI="s3://${S3_BUCKET}/${S3_PREFIX}/${ARCHIVE_NAME}"

# Optional: AWS KMS key (uncomment to use KMS instead of AES256)
# SSE_ARGS=(--sse "aws:kms" --sse-kms-key-id "arn:aws:kms:ca-central-1:123456789012:key/your-key-id")
SSE_ARGS=(--sse "AES256")

# How many local backups to keep
KEEP_LOCAL=7