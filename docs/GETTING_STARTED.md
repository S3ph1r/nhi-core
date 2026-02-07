# 🚀 Getting Started with NHI-CORE

Welcome to the Neural Home Infrastructure. This guide will take you from a "naked" MiniPC to a fully AI-managed Control Plane.

## 1. Hardware Recommendations
NHI-CORE is lightweight, but the "Brain" you connect to it later might not be.
*   **Minimal**: Intel N100/N95 MiniPC (e.g., Beelink, GMKtec), 16GB RAM, 512GB NVMe.
*   **Recommended**: Intel Core i5/i7 (8th gen+) or AMD Ryzen, 32GB+ RAM.
*   **Network**: Ethernet connection required.

## 2. Proxmox Installation (Manual Step)
Before the AI can take over, you need to install the Hypervisor.
1.  **Download**: [Proxmox VE ISO Installer](https://www.proxmox.com/en/downloads).
2.  **Flash**: Use [Rufus](https://rufus.ie/) or [BalenaEtcher](https://etcher.balena.io/) to write the ISO to a USB stick.
3.  **Install**: Boot the MiniPC from USB and follow the wizard.
    *   **Tip**: Assign a static IP (e.g., `192.168.1.2`).
    *   **Hostname**: `homelab`.
4.  **First Login**: Open `https://<YOUR-IP>:8006` in your browser. Login with `root` and the password you chose.

## 3. Prepare for the Agent
Your AI Agent needs a "door" to enter and manage Proxmox.
1.  **Create API Token**:
    *   Go to **Datacenter** → **Permissions** → **API Tokens**.
    *   Click **Add**. User: `root@pam`. Token ID: `ai-scanner`.
    *   **IMPORTANT**: Uncheck "Privilege Separation" (for full control) or assign `Administrator` role.
    *   **SAVE THE SECRET UUID**: This is shown only once!

## 4. Deploying with Antigravity (The "Magic" Part)
You don't need to manually install NHI-CORE. Your AI Agent will do it for you.

1.  **Install Antigravity** (or your preferred Agent IDE like Cursor/Cline) on your client PC.
2.  **Open a Workspace**: Point it to an empty local folder.
3.  **Feeding the Protocol**:
    *   Copy the content of [AGENTS.md](AGENTS.md).
    *   Paste it into the Agent's chat.
    *   The Agent will ask you for the Proxmox IP, Password, and the API Token you just created.
    *   Sit back and watch it deploy the LXC container and install the Core.

## 5. What's Next?

Once the Agent finishes:
1.  **Connect**: Map the shared drive `N:` via RaiDrive (Address: LXC IP, User: `ai-agent`).
2.  **Context**: Look in `N:\nhi-data\context\`. You will confirm the file `.cursorrules` is there.
3.  **Quality Assurance**: Before you start coding, run `make qa` inside any project to ensure style & type checks pass (see [Quality Assurance](QUALITY_ASSURANCE.md)).
3.  **Expand**: You can now ask the Agent to "Deploy a new Plex server" or "Set up Home Assistant", and it will use the context it just built.
