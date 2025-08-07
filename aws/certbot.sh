## CERTBOT
#
# this file is for halalcooking.ca
#
# Install python3-pip if not installed
sudo dnf install -y python3-pip

# Install certbot and route53 plugin using pip
pip3 install --user certbot certbot-dns-route53

# Run certbot with full path
~/.local/bin/certbot --version

# Obtain certificate (replace with your domain)
~/.local/bin/certbot certonly --dns-route53 -d "*.halalcooking.ca" -d "halalcooking.ca" \
  --config-dir ~/.certbot/config \
  --work-dir ~/.certbot/work \
  --logs-dir ~/.certbot/logs
