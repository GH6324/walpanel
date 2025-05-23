#!/bin/bash

REPO_URL="https://github.com/primeZdev/walpanel.git"
INSTALL_DIR="/opt/walpanel"
DONATION_ADDRESS="TWHESbRLWB9ZNoL9vcphY2r56qHeJLwtmZ"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_banner() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}${BOLD}                    WALPANEL INSTALLER                    ${NC}${BLUE}║${NC}"
    echo -e "${BLUE}╠══════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BLUE}║${NC}${CYAN} [1] Install Walpanel${NC}${BLUE}                                    ║${NC}"
    echo -e "${BLUE}║${NC}${CYAN} [2] Update Walpanel${NC}${BLUE}                                     ║${NC}"
    echo -e "${BLUE}║${NC}${CYAN} [3] Check Status${NC}${BLUE}                                        ║${NC}"
    echo -e "${BLUE}║${NC}${CYAN} [4] Donate${NC}${BLUE}                                             ║${NC}"
    echo -e "${BLUE}║${NC}${CYAN} [5] Uninstall Walpanel${NC}${BLUE}                                 ║${NC}"
    echo -e "${BLUE}║${NC}${CYAN} [0] Exit${NC}${BLUE}                                              ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo
}

check_dependencies() {
    echo -e "${BLUE}[*] Checking system dependencies...${NC}"
    apt update >/dev/null 2>&1
    apt install -y docker.io docker-compose certbot nginx git >/dev/null 2>&1 || {
        echo -e "${RED}[-] Error: Failed to install required packages${NC}"
        exit 1
    }
    systemctl enable docker >/dev/null 2>&1 && systemctl start docker >/dev/null 2>&1
    echo -e "${GREEN}[+] Dependencies installed successfully${NC}"
}

install() {
    echo -e "${BLUE}[*] Starting Walpanel installation${NC}"
    
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${YELLOW}[!] Installation directory already exists${NC}"
        return
    fi

    git clone "$REPO_URL" "$INSTALL_DIR" || {
        echo -e "${RED}[-] Error: Failed to clone repository${NC}"
        exit 1
    }

    cd "$INSTALL_DIR" || exit 1
    [ ! -f .env ] && cp .env.example .env

    echo -e "${BLUE}[*] Configuration setup${NC}"
    read -p "Enter admin username: " USERNAME
    read -p "Enter admin password: " PASSWORD
    read -p "Enter Telegram admin chat ID: " ADMIN_CHAT_ID
    read -p "Enter Telegram bot token: " BOT_TOKEN
    read -p "Enter domain/subdomain (e.g. panel.example.com): " SUBDOMAIN
    read -p "Enter port to expose (default 443): " PORT
    PORT=${PORT:-443}

    sed -i "s|USERNAME=.*|USERNAME=$USERNAME|g" .env
    sed -i "s|PASSWORD=.*|PASSWORD=$PASSWORD|g" .env
    sed -i "s|ADMIN_CHAT_ID=.*|ADMIN_CHAT_ID=$ADMIN_CHAT_ID|g" .env
    sed -i "s|BOT_TOKEN=.*|BOT_TOKEN=$BOT_TOKEN|g" .env

    echo -e "${BLUE}[*] Configuring SSL certificate${NC}"
    systemctl stop nginx >/dev/null 2>&1
    certbot certonly --standalone -d "$SUBDOMAIN" --non-interactive --agree-tos -m admin@$SUBDOMAIN || {
        echo -e "${RED}[-] Error: SSL certificate generation failed${NC}"
        systemctl start nginx >/dev/null 2>&1
        exit 1
    }
    systemctl start nginx >/dev/null 2>&1

    echo -e "${BLUE}[*] Setting up Nginx reverse proxy${NC}"
    cat > /etc/nginx/sites-available/walpanel <<EOF
server {
    listen $PORT ssl;
    server_name $SUBDOMAIN;

    ssl_certificate /etc/letsencrypt/live/$SUBDOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$SUBDOMAIN/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

    ln -sf /etc/nginx/sites-available/walpanel /etc/nginx/sites-enabled/
    nginx -t >/dev/null 2>&1 && systemctl restart nginx >/dev/null 2>&1

    echo -e "${BLUE}[*] Starting Walpanel services${NC}"
    docker-compose up -d --build >/dev/null 2>&1 || {
        echo -e "${RED}[-] Error: Failed to start containers${NC}"
        exit 1
    }

    echo -e "${GREEN}[+] Installation completed successfully${NC}"
    echo -e "${GREEN}[+] Access your panel at: https://$SUBDOMAIN${PORT:+:$PORT}/login/${NC}"
}

update() {
    echo -e "${BLUE}[*] Updating Walpanel${NC}"
    
    if [ ! -d "$INSTALL_DIR" ]; then
        echo -e "${RED}[-] Error: Walpanel not installed${NC}"
        return
    fi

    cd "$INSTALL_DIR" || exit 1
    git pull >/dev/null 2>&1
    docker-compose down >/dev/null 2>&1
    docker-compose up -d --build >/dev/null 2>&1
    
    echo -e "${GREEN}[+] Update completed successfully${NC}"
}

uninstall() {
    echo -e "${YELLOW}[!] Uninstalling Walpanel${NC}"
    
    if [ ! -d "$INSTALL_DIR" ]; then
        echo -e "${RED}[-] Error: Walpanel not installed${NC}"
        return
    fi

    cd "$INSTALL_DIR" || exit 1
    docker-compose down >/dev/null 2>&1
    rm -f /etc/nginx/sites-available/walpanel /etc/nginx/sites-enabled/walpanel /opt/walpanel
    systemctl restart nginx >/dev/null 2>&1
    
    echo -e "${GREEN}[+] Uninstallation completed${NC}"
}

status() {
    echo -e "${BLUE}[*] Current Walpanel status${NC}"
    docker ps --filter name=walpanel --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"
}

donate() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}${BOLD}                      SUPPORT WALPANEL                     ${NC}${BLUE}║${NC}"
    echo -e "${BLUE}╠══════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BLUE}║${NC} Your support helps us continue developing and improving${NC}${BLUE}║${NC}"
    echo -e "${BLUE}║${NC} Walpanel. Every contribution makes a difference!     ${NC}${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}                                                    ${NC}${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}${YELLOW} Donate (TRON - TRC20):${NC}${BLUE}                              ║${NC}"
    echo -e "${BLUE}║${NC}${GREEN} $DONATION_ADDRESS${NC}${BLUE}                    ║${NC}"
    echo -e "${BLUE}║${NC}                                                    ${NC}${BLUE}║${NC}"
    echo -e "${BLUE}║${NC} Thank you for your support!                         ${NC}${BLUE}║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Main menu
while true; do
    print_banner
    read -p "Select an option [0-5]: " opt
    case $opt in
        1) check_dependencies && install ;;
        2) update ;;
        3) status ;;
        4) donate ;;
        5) uninstall ;;
        0) echo -e "${GREEN}Exiting...${NC}"; exit 0 ;;
        *) echo -e "${RED}Invalid selection${NC}" ;;
    esac
    read -p "Press [Enter] to continue..."
done