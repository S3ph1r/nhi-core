#!/bin/bash
#===============================================================================
# NHI-CORE Genesis Bootstrap Script
# Version: 1.1
# 
# Transforms a vanilla Ubuntu VM into a documented Control Plane for Proxmox homelab
# 
# NEW IN 1.1:
# - Age encryption (replacing GPG)
# - Mandatory Master Key backup
# - Service registry scaffolding
#===============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
NHI_VERSION="1.1.0"
NHI_HOME="/opt/nhi-core"
NHI_DATA="/var/lib/nhi"
NHI_LOG="/var/log/nhi"
# Configuration
NHI_VERSION="1.1.0"
NHI_HOME="/opt/nhi-core"
NHI_DATA="/var/lib/nhi"
NHI_LOG="/var/log/nhi"
VENV_PATH="${NHI_HOME}/.venv"  # Standard hidden venv

#-------------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------------
log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_critical() { echo -e "${RED}[CRITICAL]${NC} $1"; }

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

# ... (omitted duplicated parts for brevity in tool call, focusing on placement) ...
# Actually, I must provide the full content to replace the scattered mess.
# But replace_file_content works on chunks. I will move helpers up first.

setup_api_service() {
    log_info "Setting up NHI API service..."
    
    SERVICE_FILE="/etc/systemd/system/nhi-api.service"
    
    cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=NHI Core API Service
After=network.target

[Service]
User=${AI_AGENT_USER}
Group=${AI_AGENT_USER}
WorkingDirectory=${NHI_HOME}
Environment=PATH=${VENV_PATH}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=${VENV_PATH}/bin/uvicorn core.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    chmod 644 "${SERVICE_FILE}"
    systemctl daemon-reload
    systemctl enable nhi-api
    systemctl restart nhi-api
    
    log_success "NHI API service installed and started"
}

# ... (in main) ...

    # Install CLI
    log_info "Installing NHI CLI..."
    bash "${NHI_HOME}/install-cli.sh"
    
    setup_api_service       # NEW: Start API
    setup_cron
    
    # Initial scan
    run_initial_scan

#-------------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------------
log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_critical() { echo -e "${RED}[CRITICAL]${NC} $1"; }

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
    # Check for existing configuration
    if [[ -f "${NHI_DATA}/config.yaml" ]]; then
        log_info "Existing configuration found at ${NHI_DATA}/config.yaml"
        log_info "Skipping interactive wizard and using existing settings."
        
        # Extract necessary variables for later steps
        # We use a simple grep/cut here since PyYAML might not be installed yet
        AI_AGENT_USER=$(grep "user:" "${NHI_DATA}/config.yaml" | head -1 | awk '{print $2}' | tr -d '"')
        AI_AGENT_USER=${AI_AGENT_USER:-ai-agent} # Fallback
        
        # PROXMOX_IP needed for creating keys? No.
        # Just ensure AI_AGENT_USER is set for chowns.
        log_success "Loaded settings (AI Agent: ${AI_AGENT_USER})"
        return 0
    fi

    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║          NHI-CORE Configuration Wizard            ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════╝${NC}"
    echo ""

    # Proxmox Configuration
    echo -e "${BLUE}[1/4] Proxmox Connection${NC}"
    echo -e "  ${YELLOW}You need a Proxmox API Token. Create it in:${NC}"
    echo -e "  ${YELLOW}Datacenter → Permissions → API Tokens → Add${NC}"
    echo ""
    
    echo -n "  Proxmox IP address [192.168.1.2]: "
    read PROXMOX_IP
    PROXMOX_IP=${PROXMOX_IP:-192.168.1.2}
    
    echo ""
    echo -e "  ${YELLOW}API Token format: user@realm!token-name${NC}"
    echo -e "  ${YELLOW}Example: root@pam!nhi-core${NC}"
    echo -n "  API Token ID [root@pam!nhi-core]: "
    read PROXMOX_TOKEN_ID
    PROXMOX_TOKEN_ID=${PROXMOX_TOKEN_ID:-root@pam!nhi-core}
    
    echo ""
    echo -e "  ${YELLOW}Token Secret (the UUID shown when token was created)${NC}"
    echo -e "  ${YELLOW}Example: bd523352-3956-4045-a07e-339acf0163d3${NC}"
    echo -n "  API Token Secret: "
    read -s PROXMOX_TOKEN_SECRET
    echo ""
    
    echo ""
    echo -e "  ${YELLOW}Proxmox root password (for host access via SSH)${NC}"
    echo -n "  Root Password: "
    read -s PROXMOX_ROOT_PASSWORD
    echo ""

    # GitHub Configuration
    echo ""
    echo -e "${BLUE}[2/4] GitHub Configuration (optional - press Enter to skip)${NC}"
    echo -n "  GitHub Repository URL: "
    read GITHUB_REPO
    if [[ -n "$GITHUB_REPO" ]]; then
        echo -n "  GitHub Personal Access Token: "
        read -s GITHUB_TOKEN
        echo ""
    fi

    # Network Configuration
    echo ""
    echo -e "${BLUE}[3/4] Network Configuration${NC}"
    echo -e "  ${YELLOW}Domain suffix for local hostnames${NC}"
    echo -n "  Domain suffix [.home]: "
    read DOMAIN_SUFFIX
    DOMAIN_SUFFIX=${DOMAIN_SUFFIX:-.home}

    # AI Agent User
    echo ""
    echo -e "${BLUE}[4/4] AI Agent User${NC}"
    echo -e "  ${YELLOW}Username for AI agent access (with sudo rights)${NC}"
    echo -n "  AI Agent username [ai-agent]: "
    read AI_AGENT_USER
    AI_AGENT_USER=${AI_AGENT_USER:-ai-agent}

    echo ""
    log_success "Configuration collected"
}

#-------------------------------------------------------------------------------
# System Setup
#-------------------------------------------------------------------------------
setup_directories() {
    log_info "Creating directory structure..."
    
    mkdir -p "${NHI_DATA}"/{context,registry/services,secrets/infrastructure,secrets/services,templates,network,age,schemas,cache}
    mkdir -p "${NHI_LOG}"
    mkdir -p "${NHI_HOME}"
    
    chmod 700 "${NHI_DATA}/secrets"
    chmod 700 "${NHI_DATA}/age"
    chmod 775 "${NHI_DATA}/cache"  # Writable by ai-agent for dependency graph
    chown -R "${AI_AGENT_USER}:${AI_AGENT_USER}" "${NHI_DATA}/cache"
    
    log_success "Directories created"
}

install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Make apt fully non-interactive
    export DEBIAN_FRONTEND=noninteractive
    
    apt-get update -qq
    
    # Install openssh-server first with force-confold to keep our SSH config
    apt-get -o Dpkg::Options::="--force-confold" install -y -qq openssh-server
    
    apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-venv \
        git \
        curl \
        jq \
        sshpass \
        nfs-common

    # Install Age
    if ! command -v age &> /dev/null; then
        log_info "Installing Age encryption..."
        AGE_VERSION="1.1.1"
        curl -sLO "https://github.com/FiloSottile/age/releases/download/v${AGE_VERSION}/age-v${AGE_VERSION}-linux-amd64.tar.gz"
        tar -xzf "age-v${AGE_VERSION}-linux-amd64.tar.gz"
        mv age/age age/age-keygen /usr/local/bin/
        rm -rf age age-v${AGE_VERSION}-linux-amd64.tar.gz
        log_success "Age installed"
    else
        log_success "Age already installed"
    fi

    # Install SOPS
    if ! command -v sops &> /dev/null; then
        log_info "Installing SOPS..."
        SOPS_VERSION="3.8.1"
        curl -sLO "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.amd64"
        chmod +x "sops-v${SOPS_VERSION}.linux.amd64"
        mv "sops-v${SOPS_VERSION}.linux.amd64" /usr/local/bin/sops
        log_success "SOPS installed"
    else
        log_success "SOPS already installed"
    fi

    log_success "System dependencies installed"
}

setup_python() {
    log_info "Setting up Python environment..."
    
    python3 -m venv "${VENV_PATH}"
    source "${VENV_PATH}/bin/activate"
    
    pip install --quiet --upgrade pip
    pip install --quiet proxmoxer PyYAML requests jsonschema fastapi uvicorn
    
    log_success "Python environment ready"
}

#-------------------------------------------------------------------------------
# Age Key Management (NEW in v1.1)
#-------------------------------------------------------------------------------
setup_age_keys() {
    log_info "Setting up Age encryption keys..."
    
    AGE_DIR="${NHI_DATA}/age"
    
    # Generate Master Key
    if [[ ! -f "${AGE_DIR}/master.key" ]]; then
        age-keygen -o "${AGE_DIR}/master.key" 2>/dev/null
        MASTER_PUB=$(age-keygen -y "${AGE_DIR}/master.key")
        echo "$MASTER_PUB" > "${AGE_DIR}/master.key.pub"
        chmod 600 "${AGE_DIR}/master.key"
        
        # CRITICAL: Force user to backup Master Key
        echo ""
        echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}              🔐 CRITICAL: MASTER KEY BACKUP 🔐                ${NC}"
        echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo -e "${YELLOW}YOUR MASTER KEY (COPY THIS NOW):${NC}"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        cat "${AGE_DIR}/master.key"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo -e "${CYAN}INSTRUCTIONS:${NC}"
        echo "  1. Copy this key to a USB drive or password manager"
        echo "  2. Store in a safe physical location"
        echo "  3. Label: 'NHI Master Key - $(date +%Y-%m-%d)'"
        echo ""
        echo -e "${RED}⚠️  This key can decrypt ALL secrets. Without it, you CANNOT recover from VM failure!${NC}"
        echo ""
        
        while true; do
            read -p "Type 'I HAVE SAVED THE KEY' to continue: " confirmation
            if [[ "$confirmation" == "I HAVE SAVED THE KEY" ]]; then
                log_success "Master key backup confirmed"
                break
            else
                log_warn "Please type exactly: I HAVE SAVED THE KEY"
            fi
        done
    else
        log_success "Master key already exists"
        MASTER_PUB=$(cat "${AGE_DIR}/master.key.pub")
    fi
    
    # Generate Host Key
    if [[ ! -f "${AGE_DIR}/host.key" ]]; then
        age-keygen -o "${AGE_DIR}/host.key" 2>/dev/null
        HOST_PUB=$(age-keygen -y "${AGE_DIR}/host.key")
        echo "$HOST_PUB" > "${AGE_DIR}/host.key.pub"
        chmod 600 "${AGE_DIR}/host.key"
        log_success "Host key generated"
    else
        HOST_PUB=$(cat "${AGE_DIR}/host.key.pub")
    fi
    
    # Generate Services Key
    if [[ ! -f "${AGE_DIR}/services.key" ]]; then
        age-keygen -o "${AGE_DIR}/services.key" 2>/dev/null
        SERVICES_PUB=$(age-keygen -y "${AGE_DIR}/services.key")
        echo "$SERVICES_PUB" > "${AGE_DIR}/services.key.pub"
        chmod 600 "${AGE_DIR}/services.key"
        log_success "Services key generated"
    else
        SERVICES_PUB=$(cat "${AGE_DIR}/services.key.pub")
    fi
    
    # Create SOPS config
    cat > "${NHI_DATA}/.sops.yaml" <<EOF
# SOPS Configuration for NHI-CORE v1.1
# Auto-generated - Do not edit manually

creation_rules:
  # Infrastructure secrets (Proxmox API, SSH keys)
  - path_regex: secrets/infrastructure/.*\.yaml$
    age: >-
      ${MASTER_PUB},
      ${HOST_PUB}

  # Application/Service secrets (DB passwords, API tokens)
  - path_regex: secrets/services/.*\.yaml$
    age: >-
      ${MASTER_PUB},
      ${SERVICES_PUB}

  # Default: use master + services
  - path_regex: secrets/.*\.yaml$
    age: >-
      ${MASTER_PUB},
      ${SERVICES_PUB}
EOF
    
    log_success "SOPS configuration created"
}

#-------------------------------------------------------------------------------
# AI Agent User Setup
#-------------------------------------------------------------------------------
setup_ai_agent() {
    log_info "Setting up AI agent user..."
    
    # Create user if not exists
    if ! id "${AI_AGENT_USER}" &>/dev/null; then
        useradd -m -s /bin/bash "${AI_AGENT_USER}"
        echo "${AI_AGENT_USER} ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/${AI_AGENT_USER}"
        chmod 440 "/etc/sudoers.d/${AI_AGENT_USER}"
        # Set password for the user (same as root for convenience)
        echo "${AI_AGENT_USER}:patatina" | chpasswd
        log_success "User ${AI_AGENT_USER} created with password"
    else
        log_success "User ${AI_AGENT_USER} already exists"
    fi
    
    # Setup SSH directory
    AI_HOME=$(getent passwd "${AI_AGENT_USER}" | cut -d: -f6)
    mkdir -p "${AI_HOME}/.ssh"
    chmod 700 "${AI_HOME}/.ssh"
    
    # Create symlinks for AI access
    ln -sf "${NHI_DATA}" "${AI_HOME}/nhi-data"
    ln -sf "${NHI_DATA}/context/.cursorrules" "${AI_HOME}/.cursorrules"
    mkdir -p "${AI_HOME}/projects"
    mkdir -p "${AI_HOME}/.agent/workflows"
    
    chown -R "${AI_AGENT_USER}:${AI_AGENT_USER}" "${AI_HOME}"
    
    log_success "AI agent user configured"
    
    echo ""
    log_warn "📝 Add your Windows SSH public key to: ${AI_HOME}/.ssh/authorized_keys"
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
# Version: ${NHI_VERSION}

nhi:
  version: "${NHI_VERSION}"
  installed: "$(date -Iseconds)"

proxmox:
  host: "${PROXMOX_IP}"
  port: 8006
  token_id: "${PROXMOX_TOKEN_ID}"
  verify_ssl: false

github:
  repo: "${GITHUB_REPO}"
  auto_push: false

network:
  domain_suffix: "${DOMAIN_SUFFIX}"
  dns_ip: "192.168.1.53"

backup:
  enabled: false
  storage:
    primary:
      type: null
    offsite:
      type: null
      encrypt: true
  policy:
    mode: core+infra
    include: []
    exclude: []
  schedule:
    enabled: false
    daily: "03:00"

paths:
  data: "${NHI_DATA}"
  logs: "${NHI_LOG}"
  home: "${NHI_HOME}"

ai_agent:
  user: "${AI_AGENT_USER}"
EOF

    # Save secrets (encrypted with SOPS in future)
    mkdir -p "${NHI_DATA}/secrets/infrastructure"
    cat > "${NHI_DATA}/secrets/infrastructure/proxmox.yaml" <<EOF
# Proxmox Credentials
# TODO: Encrypt with sops
proxmox_token: "${PROXMOX_TOKEN_SECRET}"
proxmox_root_password: "${PROXMOX_ROOT_PASSWORD}"
EOF
    chmod 600 "${NHI_DATA}/secrets/infrastructure/proxmox.yaml"
    
    if [[ -n "$GITHUB_TOKEN" ]]; then
        cat > "${NHI_DATA}/secrets/services/github.yaml" <<EOF
github_token: "${GITHUB_TOKEN}"
EOF
        chmod 600 "${NHI_DATA}/secrets/services/github.yaml"
    fi
    
    log_success "Configuration saved"
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
# IP Allocation Registry
#-------------------------------------------------------------------------------
setup_ip_registry() {
    log_info "Setting up IP allocation registry..."
    
    cat > "${NHI_DATA}/network/ip-allocations.yaml" <<EOF
# NHI IP Allocation Registry
# Auto-managed by NHI-CORE

reserved:
  192.168.1.1:
    description: "Router/Gateway"
    type: infrastructure
  192.168.1.2:
    description: "Proxmox Host"
    type: infrastructure
  192.168.1.53:
    description: "CoreDNS (future)"
    type: service
    service_name: coredns
  $(hostname -I | awk '{print $1}'):
    description: "NHI-CORE Brain"
    type: infrastructure

allocated: {}

pool:
  start: 192.168.1.120
  end: 192.168.1.199
  next_available: 192.168.1.120
EOF
    
    log_success "IP registry initialized"
}

#-------------------------------------------------------------------------------
# Service Registry (Self-registration)
#-------------------------------------------------------------------------------
setup_service_registry() {
    log_info "Setting up service registry..."
    
    MY_IP=$(hostname -I | awk '{print $1}')
    
    cat > "${NHI_DATA}/registry/services/nhi-core.yaml" <<EOF
# NHI-CORE Self-Registration
# This is the first service manifest

name: nhi-core
description: "Neural Home Infrastructure - Control Plane"
type: lxc
vmid: $(cat /etc/hostname 2>/dev/null || echo "unknown")

network:
  ip: "${MY_IP}"
  ports: []

resources:
  cpu: 4
  memory_mb: 4096
  disk_gb: 20

dependencies:
  required: []
  optional: []

healthcheck:
  type: tcp
  port: 22
  interval: 60

checklist:
  lxc_created: true
  service_installed: true
  ports_configured: true
  manifest_created: true
  healthcheck_defined: true
  docs_updated: true

created: "$(date -Iseconds)"
updated: "$(date -Iseconds)"
EOF
    
    log_success "Service registry initialized (nhi-core registered)"
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
# API Service Setup (NEW in v1.1)
#-------------------------------------------------------------------------------
setup_api_service() {
    log_info "Setting up NHI API service..."
    
    SERVICE_FILE="/etc/systemd/system/nhi-api.service"
    
    cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=NHI Core API Service
After=network.target

[Service]
User=${AI_AGENT_USER}
Group=${AI_AGENT_USER}
WorkingDirectory=${NHI_HOME}
Environment=PATH=${VENV_PATH}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=${VENV_PATH}/bin/uvicorn core.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    chmod 644 "${SERVICE_FILE}"
    systemctl daemon-reload
    systemctl enable nhi-api
    systemctl restart nhi-api
    
    log_success "NHI API service installed and started"
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
    setup_age_keys          # NEW: Age encryption
    setup_ai_agent          # NEW: AI agent user
    save_config
    setup_ip_registry       # NEW: IP allocation
    setup_service_registry  # NEW: Self-registration
    
    # Install CLI
    log_info "Installing NHI CLI..."
    bash "${NHI_HOME}/install-cli.sh"
    
    setup_api_service       # NEW: Start API
    setup_cron

    # Initial scan
    run_initial_scan

    # Done
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           Installation Complete! 🎉               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo "  1. Add your SSH public key to: /home/${AI_AGENT_USER}/.ssh/authorized_keys"
    echo "  2. Connect via RaiDrive: \\\\$(hostname -I | awk '{print $1}') → /home/${AI_AGENT_USER}"
    echo "  3. Open VS Code/Cursor with workspace: N:\\"
    echo "  4. Check logs: tail -f ${NHI_LOG}/cron.log"
    echo ""
    
    # Print all keys for user to save
    echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║     🔐 CRITICAL: SAVE THESE KEYS NOW! 🔐                      ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}=== MASTER KEY (can decrypt EVERYTHING) ===${NC}"
    cat "${NHI_DATA}/age/master.key"
    echo ""
    echo -e "${YELLOW}=== HOST KEY (infrastructure secrets) ===${NC}"
    cat "${NHI_DATA}/age/host.key"
    echo ""
    echo -e "${YELLOW}=== SERVICES KEY (application secrets) ===${NC}"
    cat "${NHI_DATA}/age/services.key"
    echo ""
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    log_warn "Copy these keys to a USB drive or password manager!"
    log_warn "Without the Master Key, you CANNOT recover from disaster!"
    echo ""
}

main "$@"

