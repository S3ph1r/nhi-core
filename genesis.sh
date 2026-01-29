#!/bin/bash
#===============================================================================
# NHI-CORE Genesis Bootstrap Script
# Version: 1.0
# 
# Transforms a vanilla Ubuntu VM into a documented Control Plane for Proxmox homelab
#===============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NHI_VERSION="1.0.0"
NHI_HOME="/opt/nhi-core"
NHI_DATA="/var/lib/nhi"
NHI_LOG="/var/log/nhi"
VENV_PATH="${NHI_HOME}/venv"

#-------------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------------
log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
    log_success "Running as root"
}

check_os() {
    if [[ ! -f /etc/os-release ]]; then
        log_error "Cannot detect OS"
        exit 1
    fi
    source /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        log_error "This script requires Ubuntu (detected: $ID)"
        exit 1
    fi
    log_success "OS: Ubuntu $VERSION_ID"
}

check_internet() {
    if ! ping -c 1 8.8.8.8 &> /dev/null; then
        log_error "No internet connectivity"
        exit 1
    fi
    log_success "Internet connectivity OK"
}

#-------------------------------------------------------------------------------
# Input Collection
#-------------------------------------------------------------------------------
collect_inputs() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          NHI-CORE Configuration Wizard            ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
    echo ""

    # Proxmox Configuration
    read -p "Proxmox IP [192.168.1.2]: " PROXMOX_IP
    PROXMOX_IP=${PROXMOX_IP:-192.168.1.2}

    read -p "Proxmox API Token ID [root@pam!nhi-core]: " PROXMOX_TOKEN_ID
    PROXMOX_TOKEN_ID=${PROXMOX_TOKEN_ID:-root@pam!nhi-core}

    read -s -p "Proxmox Token Secret: " PROXMOX_TOKEN_SECRET
    echo ""

    # GitHub Configuration
    read -p "GitHub Repository URL: " GITHUB_REPO
    read -s -p "GitHub Personal Access Token: " GITHUB_TOKEN
    echo ""

    # Network Configuration
    read -p "Domain suffix [.home]: " DOMAIN_SUFFIX
    DOMAIN_SUFFIX=${DOMAIN_SUFFIX:-.home}

    # SMB Configuration
    read -p "SMB Share User [nhi-user]: " SMB_USER
    SMB_USER=${SMB_USER:-nhi-user}

    read -s -p "SMB Share Password: " SMB_PASSWORD
    echo ""

    log_success "Configuration collected"
}

#-------------------------------------------------------------------------------
# System Setup
#-------------------------------------------------------------------------------
setup_directories() {
    log_info "Creating directory structure..."
    
    mkdir -p "${NHI_DATA}"/{context,registry,secrets,templates}
    mkdir -p "${NHI_LOG}"
    mkdir -p "${NHI_HOME}"
    
    chmod 700 "${NHI_DATA}/secrets"
    
    log_success "Directories created"
}

install_dependencies() {
    log_info "Installing system dependencies..."
    
    apt-get update -qq
    apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-venv \
        git \
        gnupg2 \
        samba \
        curl \
        jq

    # Install SOPS
    if ! command -v sops &> /dev/null; then
        log_info "Installing SOPS..."
        SOPS_VERSION="3.8.1"
        curl -sLO "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.amd64"
        chmod +x "sops-v${SOPS_VERSION}.linux.amd64"
        mv "sops-v${SOPS_VERSION}.linux.amd64" /usr/local/bin/sops
    fi

    log_success "System dependencies installed"
}

setup_python() {
    log_info "Setting up Python environment..."
    
    python3 -m venv "${VENV_PATH}"
    source "${VENV_PATH}/bin/activate"
    
    pip install --quiet --upgrade pip
    pip install --quiet proxmoxer PyYAML requests python-gnupg
    
    log_success "Python environment ready"
}

#-------------------------------------------------------------------------------
# Clone/Update Repository
#-------------------------------------------------------------------------------
setup_repository() {
    log_info "Setting up NHI-CORE repository..."
    
    if [[ -d "${NHI_HOME}/.git" ]]; then
        cd "${NHI_HOME}"
        git pull --quiet
        log_success "Repository updated"
    else
        # Clone if GITHUB_REPO is provided, otherwise assume local install
        if [[ -n "${GITHUB_REPO}" ]]; then
            git clone --quiet "${GITHUB_REPO}" "${NHI_HOME}" || true
        fi
        log_success "Repository ready"
    fi
}

#-------------------------------------------------------------------------------
# GPG & SOPS Setup
#-------------------------------------------------------------------------------
setup_gpg() {
    log_info "Setting up GPG key..."
    
    # Check if key already exists
    if gpg --list-keys "nhi@localhost" &> /dev/null; then
        log_warn "GPG key already exists, skipping generation"
        return
    fi

    # Generate key
    cat > /tmp/gpg-batch <<EOF
Key-Type: RSA
Key-Length: 4096
Name-Real: NHI Core
Name-Email: nhi@localhost
Expire-Date: 2y
%no-protection
%commit
EOF

    gpg --batch --gen-key /tmp/gpg-batch
    rm /tmp/gpg-batch
    
    # Get fingerprint
    GPG_FINGERPRINT=$(gpg --list-keys --with-colons "nhi@localhost" | grep fpr | head -1 | cut -d: -f10)
    
    # Create SOPS config
    cat > "${NHI_DATA}/.sops.yaml" <<EOF
creation_rules:
  - path_regex: secrets/.*\.yaml$
    pgp: '${GPG_FINGERPRINT}'
EOF
    
    log_success "GPG key generated (fingerprint: ${GPG_FINGERPRINT:0:16}...)"
    
    # Backup reminder
    echo ""
    log_warn "🔑 CRITICAL: Backup your GPG key NOW!"
    echo "   Run: gpg --export-secret-keys --armor > /tmp/nhi-backup-key.asc"
    echo ""
}

#-------------------------------------------------------------------------------
# Save Configuration
#-------------------------------------------------------------------------------
save_config() {
    log_info "Saving configuration..."
    
    cat > "${NHI_DATA}/config.yaml" <<EOF
# NHI-CORE Configuration
# Generated: $(date -Iseconds)

proxmox:
  host: "${PROXMOX_IP}"
  port: 8006
  token_id: "${PROXMOX_TOKEN_ID}"
  verify_ssl: false

github:
  repo: "${GITHUB_REPO}"

network:
  domain_suffix: "${DOMAIN_SUFFIX}"

paths:
  data: "${NHI_DATA}"
  logs: "${NHI_LOG}"
  home: "${NHI_HOME}"
EOF

    # Save token secret encrypted (for now, plain - will use SOPS)
    echo "${PROXMOX_TOKEN_SECRET}" > "${NHI_DATA}/secrets/.proxmox_token"
    echo "${GITHUB_TOKEN}" > "${NHI_DATA}/secrets/.github_token"
    chmod 600 "${NHI_DATA}/secrets/."*
    
    log_success "Configuration saved"
}

#-------------------------------------------------------------------------------
# SMB Setup
#-------------------------------------------------------------------------------
setup_smb() {
    log_info "Configuring SMB share..."
    
    # Create SMB user
    useradd -M -s /sbin/nologin "${SMB_USER}" 2>/dev/null || true
    echo -e "${SMB_PASSWORD}\n${SMB_PASSWORD}" | smbpasswd -a -s "${SMB_USER}"
    
    # Configure Samba
    cat >> /etc/samba/smb.conf <<EOF

[nhi-registry]
   comment = NHI Registry Share
   path = ${NHI_DATA}
   browseable = yes
   read only = no
   valid users = ${SMB_USER}
   create mask = 0644
   directory mask = 0755
EOF
    
    systemctl restart smbd
    systemctl enable smbd
    
    log_success "SMB share configured: \\\\$(hostname -I | awk '{print $1}')\\nhi-registry"
}

#-------------------------------------------------------------------------------
# Cron Setup
#-------------------------------------------------------------------------------
setup_cron() {
    log_info "Setting up automatic updates..."
    
    CRON_CMD="0 * * * * root ${VENV_PATH}/bin/python ${NHI_HOME}/core/context/updater.py >> ${NHI_LOG}/cron.log 2>&1"
    
    echo "${CRON_CMD}" > /etc/cron.d/nhi-core
    chmod 644 /etc/cron.d/nhi-core
    
    log_success "Cron job installed (hourly updates)"
}

#-------------------------------------------------------------------------------
# Initial Scan
#-------------------------------------------------------------------------------
run_initial_scan() {
    log_info "Running initial infrastructure scan..."
    
    source "${VENV_PATH}/bin/activate"
    cd "${NHI_HOME}"
    
    python3 -c "
from core.scanner import ProxmoxScanner
from core.context import ContextGenerator

scanner = ProxmoxScanner()
infrastructure = scanner.scan_all()

generator = ContextGenerator(infrastructure)
generator.generate()
print('Initial scan complete!')
" 2>&1 | tee -a "${NHI_LOG}/install.log"
    
    log_success "Initial scan complete"
}

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------
main() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║      NHI-CORE Genesis Bootstrap v${NHI_VERSION}            ║${NC}"
    echo -e "${GREEN}║   Neural Home Infrastructure - Control Plane      ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
    echo ""

    # Dry run mode
    if [[ "$1" == "--dry-run" ]]; then
        log_info "DRY RUN MODE - No changes will be made"
        check_root
        check_os
        check_internet
        log_success "All prerequisites OK. Ready to install."
        exit 0
    fi

    # Prerequisites
    check_root
    check_os
    check_internet

    # Collect configuration
    collect_inputs

    # Setup
    setup_directories
    install_dependencies
    setup_python
    setup_repository
    setup_gpg
    save_config
    setup_smb
    setup_cron

    # Initial scan
    run_initial_scan

    # Done
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           Installation Complete! 🎉               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Backup GPG key: gpg --export-secret-keys --armor > ~/nhi-backup.asc"
    echo "  2. Connect from Windows via: \\\\$(hostname -I | awk '{print $1}')\\nhi-registry"
    echo "  3. Check logs: tail -f ${NHI_LOG}/cron.log"
    echo ""
}

main "$@"
