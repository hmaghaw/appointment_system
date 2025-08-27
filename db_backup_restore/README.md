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

# To Install a new version of db
```angular2html
docker compose down -v          # removes containers and named volumes (you’re using a bind mount, so next step too)
sudo rm -rf ../db_data/*       
```

# In test environment
```angular2html
aws s3 cp s3://polydial/mysql-backups/mysql_data_2025-08-14_193413.tar.gz .
aws s3 cp s3://polydial/mysql-backups/mysql_data_2025-08-14_193413.tar.gz.sha256 .
tar -xvzf C:\Users\HanyE\PycharmProjects\windsurf_appointment_system\db_backup_restore\mysql_data_2025-08-14_193413.tar.gz



```