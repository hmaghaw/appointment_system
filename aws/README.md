## Install Docker and docker-compose
```angular2html
chmod +x install_docker.sh
. install_docker.sh
```
## Elastic IP
```angular2html
98.86.217.185
```

# Create Nginx Config
```angular2html
sudo dnf install -y nginx

sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl status nginx

```

```angular2html
sudo nano /etc/nginx/conf.d/halalcooking.ca.conf
```

```angular2html
# Redirect HTTP to HTTPS for both subdomains
server {
    listen 80;
    server_name api.www.halalcooking.ca twilio.halalcooking.ca;

    return 301 https://$host$request_uri;
}

# ======================
# API Service (Port 5000)
# ======================
server {
    listen 443 ssl;
    server_name api.www.halalcooking.ca;

    ssl_certificate     /home/ec2-user/.certbot/config/live/halalcooking.ca/fullchain.pem;
    ssl_certificate_key /home/ec2-user/.certbot/config/live/halalcooking.ca/privkey.pem;

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
    server_name twilio.halalcooking.ca;

    ssl_certificate     /home/ec2-user/.certbot/config/live/halalcooking.ca/fullchain.pem;
    ssl_certificate_key /home/ec2-user/.certbot/config/live/halalcooking.ca/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

```https://api.halalcooking.ca

```angular2html
sudo systemctl reload nginx 
```