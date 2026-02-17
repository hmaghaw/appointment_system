## Install Docker and docker-compose
```angular2html
chmod +x install_docker.sh
. install_docker.sh
```
## Elastic IP
```angular2html
34.199.192.157
```

# Create Nginx Config
```angular2html
sudo dnf install -y nginx

sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl status nginx

```

```angular2html
sudo nano /etc/nginx/conf.d/polydial.com.conf
```

```angular2html
# Redirect HTTP to HTTPS for all subdomains
server {
    listen 80;
    server_name api.www.polydial.com twilio.polydial.com n8n.polydial.com mcp.polydial.com;
    return 301 https://$host$request_uri;
}

# ======================
# API Service (Port 5000)
# ======================
server {
    listen 443 ssl;
    server_name api.www.polydial.com;

    ssl_certificate     /home/ec2-user/.certbot/config/live/polydial.com/fullchain.pem;
    ssl_certificate_key /home/ec2-user/.certbot/config/live/polydial.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# ==========================
# Twilio Service (Port 8000)
# ==========================
server {
    listen 443 ssl;
    server_name twilio.polydial.com;
--
    ssl_certificate     /home/ec2-user/.certbot/config/live/polydial.com/fullchain.pem;
    ssl_certificate_key /home/ec2-user/.certbot/config/live/polydial.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# ==========================
# n8n Service (Port 5678)
# ==========================
server {
    listen 443 ssl;
    server_name n8n.polydial.com;

    ssl_certificate     /home/ec2-user/.certbot/config/live/polydial.com/fullchain.pem;
    ssl_certificate_key /home/ec2-user/.certbot/config/live/polydial.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    client_max_body_size 25m;

    location / {
        proxy_pass http://localhost:5678;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        proxy_connect_timeout 60s;
        proxy_buffering off;
    }
}

```https://api.polydial.com

```angular2html
sudo systemctl reload nginx 
```

# Install Crontab
```angular2html
sudo yum install -y cronie
sudo systemctl enable crond
sudo systemctl start crond
```
```angular2html
echo 'export EDITOR=nano' >> ~/.bashrc
source ~/.bashrc
crontab -e
```
# crontab
```angular2html
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
MAILTO=""
0 2 * * * /bin/bash /home/ec2-user/appointment_system/db_backup_restore/backup_to_s3.sh >> /home/ec2-user/db_data_backup/db_backup.log 2>&1
```