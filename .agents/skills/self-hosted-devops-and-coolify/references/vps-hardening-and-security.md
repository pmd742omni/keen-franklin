# VPS Security Hardening: Debian & Ubuntu Server Baseline

> Production guide for hardening cloud VPS nodes hosting open-source web systems.

---

## 1. Automated Setup & Hardening Script

Run on a fresh Ubuntu 24.04 / Debian 12 server:

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Update OS packages
apt update && apt upgrade -y
apt install -y ufw fail2ban curl git unattended-upgrades

# 2. Configure Non-Root Deploy User
DEPLOY_USER="deployer"
if ! id "$DEPLOY_USER" &>/dev/null; then
    adduser --disabled-password --gecos "" "$DEPLOY_USER"
    usermod -aG sudo "$DEPLOY_USER"
    echo "$DEPLOY_USER ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/$DEPLOY_USER"
    mkdir -p "/home/$DEPLOY_USER/.ssh"
    cp /root/.ssh/authorized_keys "/home/$DEPLOY_USER/.ssh/"
    chown -R "$DEPLOY_USER:$DEPLOY_USER" "/home/$DEPLOY_USER/.ssh"
    chmod 700 "/home/$DEPLOY_USER/.ssh"
    chmod 600 "/home/$DEPLOY_USER/.ssh/authorized_keys"
fi

# 3. Harden SSH Configuration
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# 4. Configure UFW Firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw --force enable

# 5. Enable and start Fail2Ban
systemctl enable fail2ban
systemctl start fail2ban

echo "VPS Hardening complete. System secured."
```
