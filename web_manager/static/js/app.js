document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const qrPlaceholder = document.getElementById('qr-placeholder');
    const qrImage = document.getElementById('qr-image');
    const qrBox = document.getElementById('qr-box');
    const btnGenerateQr = document.getElementById('btn-generate-qr');
    const qrStatusMsg = document.getElementById('qr-status-msg');
    
    const configForm = document.getElementById('config-form');
    const botNameInput = document.getElementById('bot-name');
    const adminIdInput = document.getElementById('admin-id');
    const botPrefixInput = document.getElementById('bot-prefix');
    const statBotName = document.getElementById('stat-bot-name');
    
    const btnStartBot = document.getElementById('btn-start-bot');
    const btnStopBot = document.getElementById('btn-stop-bot');
    
    const sidebarStatusIndicator = document.getElementById('sidebar-status-indicator');
    const sidebarStatusText = document.getElementById('sidebar-status-text');
    const mobileStatusIndicator = document.getElementById('mobile-status-indicator');
    const mobileStatusText = document.getElementById('mobile-status-text');
    const mobileBotName = document.getElementById('mobile-bot-name');
    
    const terminalBody = document.getElementById('terminal-body');
    const btnClearConsole = document.getElementById('btn-clear-console');
    const btnAutoScroll = document.getElementById('btn-auto-scroll');
    
    // Mobile hamburger
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    
    // Application States
    let botRunning = false;
    let autoScroll = true;
    let qrPollInterval = null;
    let logsPollInterval = null;
    let statusPollInterval = null;
    
    // Library Manager elements and state
    const btnInstallAll = document.getElementById('btn-install-all');
    const btnPipInstall = document.getElementById('btn-pip-install');
    const pipPackageInput = document.getElementById('pip-package-input');
    let autoInstalledModules = new Set();
    const pkgMapping = {
        'PIL': 'pillow',
        'bs4': 'beautifulsoup4',
        'telegram': 'python-telegram-bot',
        'jwt': 'PyJWT',
        'yaml': 'pyyaml',
        'mysql': 'mysql-connector-python',
        'fitz': 'pymupdf',
        'cv2': 'opencv-python'
    };

    // ============================
    // HAMBURGER MENU
    // ============================
    function openSidebar() {
        sidebar.classList.add('open');
        sidebarOverlay.classList.add('open');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        sidebarOverlay.classList.remove('open');
        document.body.style.overflow = '';
    }

    hamburgerBtn.addEventListener('click', openSidebar);
    sidebarOverlay.addEventListener('click', closeSidebar);

    // Close sidebar when nav item clicked on mobile
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth < 768) closeSidebar();
        });
    });

    // ============================
    // INITIALIZE
    // ============================
    loadConfig();
    checkBotStatus();
    statusPollInterval = setInterval(checkBotStatus, 3000);
    logsPollInterval = setInterval(fetchLogs, 1500);

    // Event Listeners
    btnGenerateQr.addEventListener('click', generateQR);
    configForm.addEventListener('submit', saveConfig);
    btnStartBot.addEventListener('click', startBot);
    btnStopBot.addEventListener('click', stopBot);
    
    btnClearConsole.addEventListener('click', () => {
        terminalBody.innerHTML = '';
        appendTerminalLine('[SYSTEM] Màn hình console đã được xóa.', 'system');
    });
    
    btnAutoScroll.addEventListener('click', () => {
        autoScroll = !autoScroll;
        btnAutoScroll.classList.toggle('active', autoScroll);
    });

    btnInstallAll.addEventListener('click', installAllRequirements);
    btnPipInstall.addEventListener('click', () => {
        const pkg = pipPackageInput.value.trim();
        if (pkg) {
            installPackage(pkg);
            pipPackageInput.value = '';
        }
    });

    // ============================
    // HELPER FUNCTIONS
    // ============================
    function appendTerminalLine(text, type = 'normal') {
        const line = document.createElement('div');
        line.className = `terminal-line ${type}-line`;
        line.innerText = text;
        terminalBody.appendChild(line);
        // Limit log lines to 500
        while (terminalBody.children.length > 500) {
            terminalBody.removeChild(terminalBody.firstChild);
        }
        if (autoScroll) {
            terminalBody.scrollTop = terminalBody.scrollHeight;
        }
    }

    function parseAnsiColors(text) {
        return text.replace(/\033\[[0-9;]*m/g, '').replace(/\x1b\[[0-9;]*m/g, '');
    }

    function updateBotStatusUI(running) {
        botRunning = running;
        btnStartBot.disabled = running;
        btnStopBot.disabled = !running;
        
        const indicators = [sidebarStatusIndicator, mobileStatusIndicator];
        const texts = [sidebarStatusText, mobileStatusText];

        indicators.forEach(el => {
            if (el) el.classList.toggle('active', running);
        });
        texts.forEach(el => {
            if (el) {
                el.innerText = running ? 'Đang Chạy' : 'Đang Dừng';
                el.style.color = running ? 'var(--success-color)' : 'var(--danger-color)';
            }
        });
    }

    // ============================
    // API CALLS
    // ============================
    async function loadConfig() {
        try {
            const res = await fetch('/api/config');
            const data = await res.json();
            botNameInput.value = data.bot_name || 'Zalo Bot';
            adminIdInput.value = data.admin_id || '';
            botPrefixInput.value = data.prefix || '?';
            statBotName.innerText = data.bot_name || 'Zalo Bot';
            if (mobileBotName) mobileBotName.innerText = data.bot_name || 'Zalo Bot';
        } catch (err) {
            console.error('Error loading config:', err);
        }
    }

    async function saveConfig(e) {
        e.preventDefault();
        const configData = {
            bot_name: botNameInput.value,
            admin_id: adminIdInput.value,
            prefix: botPrefixInput.value
        };

        try {
            const res = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(configData)
            });
            const result = await res.json();
            if (result.status === 'success') {
                statBotName.innerText = configData.bot_name;
                if (mobileBotName) mobileBotName.innerText = configData.bot_name;
                appendTerminalLine(`[SYSTEM] ${result.message}`, 'success');
            } else {
                appendTerminalLine(`[SYSTEM ERROR] Không thể lưu cấu hình!`, 'error');
            }
        } catch (err) {
            appendTerminalLine(`[SYSTEM ERROR] Kết nối thất bại: ${err.message}`, 'error');
        }
    }

    async function generateQR() {
        btnGenerateQr.disabled = true;
        qrBox.classList.remove('has-qr');
        qrPlaceholder.innerHTML = '<i class="fa-solid fa-spinner fa-spin qr-spinner"></i><p>Đang tạo mã QR...</p>';
        qrPlaceholder.classList.remove('hidden');
        qrImage.classList.add('hidden');
        qrStatusMsg.innerHTML = '<span class="badge badge-info">Generating</span> Đang kết nối đến Zalo, vui lòng chờ...';
        
        try {
            await fetch('/api/qr/generate', { method: 'POST' });
            if (qrPollInterval) clearInterval(qrPollInterval);
            qrPollInterval = setInterval(pollQRStatus, 2000);
        } catch (err) {
            btnGenerateQr.disabled = false;
            qrStatusMsg.innerHTML = '<span class="badge badge-danger">Lỗi</span> Không thể kết nối đến server.';
        }
    }

    async function pollQRStatus() {
        try {
            const res = await fetch('/api/qr/status');
            const data = await res.json();
            
            if (data.status === 'generating') {
                qrStatusMsg.innerHTML = '<span class="badge badge-info">Generating</span> Đang tạo mã QR từ Zalo...';

            } else if (data.status === 'generated') {
                // Show QR from base64 data - no filesystem dependency!
                if (data.qr_base64) {
                    qrImage.src = 'data:image/png;base64,' + data.qr_base64;
                    qrPlaceholder.classList.add('hidden');
                    qrImage.classList.remove('hidden');
                    qrBox.classList.add('has-qr');
                }
                qrStatusMsg.innerHTML = '<span class="badge badge-info">Chờ Quét</span> Mở ứng dụng Zalo trên điện thoại → quét mã QR này để đăng nhập.';
                btnGenerateQr.disabled = false;

            } else if (data.status === 'success') {
                clearInterval(qrPollInterval);
                qrPollInterval = null;
                qrBox.classList.remove('has-qr');
                qrPlaceholder.innerHTML = '<i class="fa-solid fa-circle-check" style="font-size: 3rem; color: #3fb950;"></i><p>Đăng nhập thành công!</p>';
                qrPlaceholder.classList.remove('hidden');
                qrImage.classList.add('hidden');
                const name = data.user_info?.name || 'Zalo User';
                qrStatusMsg.innerHTML = `<span class="badge badge-success">Thành Công</span> Đã đăng nhập: <strong>${name}</strong>`;
                appendTerminalLine(`[SYSTEM] ✅ Zalo đăng nhập thành công! Tài khoản: ${name}`, 'success');
                btnGenerateQr.disabled = false;

            } else if (data.status === 'failed') {
                clearInterval(qrPollInterval);
                qrPollInterval = null;
                qrBox.classList.remove('has-qr');
                qrPlaceholder.innerHTML = '<i class="fa-solid fa-circle-xmark" style="font-size: 3rem; color: #f85149;"></i><p>Thất bại</p>';
                qrPlaceholder.classList.remove('hidden');
                qrImage.classList.add('hidden');
                qrStatusMsg.innerHTML = `<span class="badge badge-danger">Lỗi</span> ${data.error_message}`;
                appendTerminalLine(`[SYSTEM ERROR] ❌ Đăng nhập QR thất bại: ${data.error_message}`, 'error');
                btnGenerateQr.disabled = false;
            }
        } catch (err) {
            console.error('Error polling QR status:', err);
        }
    }

    async function checkBotStatus() {
        try {
            const res = await fetch('/api/bot/status');
            const data = await res.json();
            updateBotStatusUI(data.running);
        } catch (err) {
            console.error('Error checking bot status:', err);
        }
    }

    async function startBot() {
        const configData = {
            bot_name: botNameInput.value,
            admin_id: adminIdInput.value,
            prefix: botPrefixInput.value
        };

        try {
            const res = await fetch('/api/bot/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(configData)
            });
            const data = await res.json();
            if (data.status === 'success') {
                appendTerminalLine(`[SYSTEM] ${data.message}`, 'success');
                checkBotStatus();
            } else {
                appendTerminalLine(`[SYSTEM ERROR] ${data.message}`, 'error');
            }
        } catch (err) {
            appendTerminalLine(`[SYSTEM ERROR] Kết nối thất bại: ${err.message}`, 'error');
        }
    }

    async function stopBot() {
        try {
            const res = await fetch('/api/bot/stop', { method: 'POST' });
            const data = await res.json();
            if (data.status === 'success') {
                appendTerminalLine(`[SYSTEM] ${data.message}`, 'success');
                checkBotStatus();
            } else {
                appendTerminalLine(`[SYSTEM ERROR] ${data.message}`, 'error');
            }
        } catch (err) {
            appendTerminalLine(`[SYSTEM ERROR] Kết nối thất bại: ${err.message}`, 'error');
        }
    }

    async function installPackage(packageName) {
        let targetPackage = packageName.trim();
        // Map common module names to their actual pip package names if they differ
        if (pkgMapping[targetPackage]) {
            targetPackage = pkgMapping[targetPackage];
        }

        appendTerminalLine(`[SYSTEM] 📦 Đang yêu cầu cài đặt thư viện: ${targetPackage}...`, 'system');
        try {
            const res = await fetch('/api/pip/install', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ package: targetPackage })
            });
            const data = await res.json();
            if (data.status === 'success') {
                appendTerminalLine(`[SYSTEM] ${data.message}`, 'success');
            } else {
                appendTerminalLine(`[SYSTEM ERROR] ${data.message}`, 'error');
            }
        } catch (err) {
            appendTerminalLine(`[SYSTEM ERROR] Yêu cầu cài đặt thất bại: ${err.message}`, 'error');
        }
    }

    async function installAllRequirements() {
        appendTerminalLine('[SYSTEM] 📦 Đang yêu cầu cài đặt toàn bộ requirements.txt...', 'system');
        try {
            const res = await fetch('/api/pip/install-all', { method: 'POST' });
            const data = await res.json();
            if (data.status === 'success') {
                appendTerminalLine(`[SYSTEM] ${data.message}`, 'success');
            } else {
                appendTerminalLine(`[SYSTEM ERROR] ${data.message}`, 'error');
            }
        } catch (err) {
            appendTerminalLine(`[SYSTEM ERROR] Yêu cầu cài đặt thất bại: ${err.message}`, 'error');
        }
    }

    async function fetchLogs() {
        try {
            const res = await fetch('/api/bot/logs');
            const data = await res.json();
            if (data.logs) {
                const lines = data.logs.split('\n');
                lines.forEach(line => {
                    if (line.trim()) {
                        const cleanLine = parseAnsiColors(line);
                        let type = 'normal';
                        if (cleanLine.includes('[ERROR]') || cleanLine.includes('Lỗi') || cleanLine.includes('Exception') || cleanLine.includes('Error')) {
                            type = 'error';
                        } else if (cleanLine.includes('[SYSTEM]') || cleanLine.includes('Khởi động') || cleanLine.includes('SYSTEM')) {
                            type = 'system';
                        } else if (cleanLine.includes('thành công') || cleanLine.includes('SUCCESS') || cleanLine.includes('SẴN SÀNG') || cleanLine.includes('✅')) {
                            type = 'success';
                        }
                        appendTerminalLine(cleanLine, type);

                        // Tự động phát hiện lỗi thiếu thư viện và cài đặt
                        const moduleMatch = cleanLine.match(/ModuleNotFoundError:\s*No\s*module\s*named\s*['"]([^'"]+)['"]/i) || 
                                            cleanLine.match(/No\s*module\s*named\s*['"]([^'"]+)['"]/i);
                        if (moduleMatch && moduleMatch[1]) {
                            const missingModule = moduleMatch[1].trim();
                            if (!autoInstalledModules.has(missingModule)) {
                                autoInstalledModules.add(missingModule);
                                appendTerminalLine(`[SYSTEM] 💡 Phát hiện thiếu thư viện: "${missingModule}". Tự động tiến hành cài đặt...`, 'system');
                                installPackage(missingModule);
                            }
                        }
                    }
                });
            }
        } catch (err) {
            console.error('Error fetching logs:', err);
        }
    }
});
