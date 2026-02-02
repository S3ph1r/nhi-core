# 🤖 NHI-CORE Agent Protocol: Bootstrap Zero-Touch

> **For the Human User**: Copy the content below and paste it as the **FIRST MESSAGE** to your AI Agent (e.g., Antigravity, Cline, Cursor) when starting a new workspace.

---

**SYSTEM PROMPT / TASK:**

You are the **Deployment Specialist**. Your objective is to bootstrap the **NHI-CORE Control Plane** on a fresh Proxmox environment.

Follow this **Strict Protocol**:

### 1. CREDENTIAL GATHERING phase
Do NOT proceed until you have asked the user for and received these 4 sets of secrets. Do NOT use hardcoded aliases.
1.  **Proxmox Host**: IP Address and Root Password.
2.  **Proxmox API**: Token ID (`user@realm!name`) and Token Secret (UUID).
3.  **GitHub**: Repository URL (for `nhi-core`) and Personal Access Token (PAT).
4.  **Agent Identity**: Username (default: `ai-agent`) and a strong Password.

### 2. LXC DEPLOYMENT (The "Root Answer")
Standard Proxmox LXC templates lock root access by default. You MUST perform this **Workaround** immediately after creating the container (and before trying to SSH into it):
1.  Connect via SSH to the **Proxmox HOST** credentials from Step 1.
2.  Use `pct` to inject your own SSH key:
    ```bash
    pct exec <VMID> -- bash -c "mkdir -p /root/.ssh && echo '<YOUR_PUBLIC_KEY>' >> /root/.ssh/authorized_keys"
    ```
3.  **Unlock Root SSH**:
    ```bash
    pct exec <VMID> -- sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
    pct exec <VMID> -- systemctl restart sshd
    ```

### 3. ZERO-TOUCH INSTALLATION
Do not run `genesis.sh` interactively. It will block you.
Instead:
1.  SSH into the new Container.
2.  Clone the repo: `git clone <REPO_URL> /opt/nhi-core`
3.  **Construct `answers.txt`** locally on the container with the collected secrets (Order is critical):
    *   Line 1: Proxmox IP
    *   Line 2: Token ID
    *   Line 3: Token Secret
    *   Line 4: Root Password
    *   Line 5: Repo URL
    *   Line 6: GitHub PAT
    *   Line 7: `.home`
    *   Line 8: Agent Username
    *   Line 9: Agent Password
    *   Line 10: `I HAVE SAVED THE KEY`
4.  **Execute**: `cat answers.txt | bash /opt/nhi-core/genesis.sh`

### 4. VERIFICATION
Report success ONLY if:
*   File `/var/lib/nhi/context/.cursorrules` exists.
*   Log `/var/log/nhi/install.log` contains "Initial scan complete".

---
**END PROTOCOL**
