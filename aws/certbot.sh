## CERTBOT
#
# this file is for polydial.com
#
# Install python3-pip if not installed
sudo dnf install -y python3-pip

# Install certbot and route53 plugin using pip
pip3 install --user certbot certbot-dns-route53

# Run certbot with full path
~/.local/bin/certbot --version

# Obtain certificate (replace with your domain)
~/.local/bin/certbot certonly --dns-route53 -d "*.polydial.com" -d "polydial.com" \
  --config-dir ~/.certbot/config \
  --work-dir ~/.certbot/work \
  --logs-dir ~/.certbot/logs

Successfully received certificate.
Certificate is saved at: /home/ec2-user/.certbot/config/live/polydial.com/fullchain.pem
Key is saved at:         /home/ec2-user/.certbot/config/live/polydial.com/privkey.pem
This certificate expires on 2025-11-11.
These files will be updated when the certificate renews.

NEXT STEPS:
- The certificate will need to be renewed before it expires. Certbot can automatically renew the certificate in the background, but you may need to take steps to enable that functionality. See https://certbot.org/renewal-setup for instructions.

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
If you like Certbot, please consider supporting our work by:
 * Donating to ISRG / Let's Encrypt:   https://letsencrypt.org/donate
 * Donating to EFF:                    https://eff.org/donate-le
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
