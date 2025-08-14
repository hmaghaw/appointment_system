# Database Backup
## Make Scripts Executable
```angular2html
chmod +x /home/ec2-user/appointment_system/db_backup_restore/create_env_vars.sh
chmod +x /home/ec2-user/appointment_system/db_backup_restore/backup_to_s3.sh
chmod +x /home/ec2-user/appointment_system/db_backup_restore/restore_from_s3.sh
chmod +x /home/ec2-user/appointment_system/db_backup_restore/restore_latest_from_s3.sh
```

# Backup Immedialtly
```angular2html
. /home/ec2-user/appointment_system/db_backup_restore/backup_to_s3.sh

```

# Restote Latest backup
```angular2html
. /home/ec2-user/appointment_system/db_backup_restore/restore_latest_from_s3.sh
```

# Restore a specific file
```angular2html
. /home/ec2-user/appointment_system/db_backup_restore/restore_from_s3.sh mysql_data_2025-08-14_193413.tar.gz

```

# CRONJOB Backup
```angular2html

```