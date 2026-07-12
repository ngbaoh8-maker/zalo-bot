document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const qrPlaceholder = document.getElementById('qr-placeholder');
    const qrImage = document.getElementById('qr-image');
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
    
    const terminalBody = document.getElementById('terminal-body');
    const btnClearConsole = document.getElementById('btn-clear-console');
    const btnAutoScroll = document.getElementById('btn-auto-scroll');
    
    // Application States
    let botRunning = false;
    let autoScroll = true;
    let qrPollInterval = null;
    let logsPollInterval = null;
    let statusPollInterval = null;

    // Initialize Page
    loadConfig();
    checkBotStatus();
    
    // Poll Bot Status, Logs every few seconds
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

    // Helper functions
    function appendTerminalLine(text, type = 'normal') {
        const line = document.createElement('div');
        line.className = `terminal-line ${type}-line`;
        line.innerText = text;
        terminalBody.appendChild(line);
        if (autoScroll) {
            terminalBody.scrollTop = terminalBody.scrollHeight;
        }
    }

    function parseAnsiColors(text) {
        // Strip out ANSI color codes for clean reading
        return text.replace(/\033\[[0-9;]*m/g, '')
                   .replace(/\x1b\[[0-9;]*m/g, '');
    }

    // API Calls
    async function loadConfig() {
        try {
            const res = await fetch('/api/config');
            const data = await res.json();
            botNameInput.value = data.bot_name || 'Zalo Bot';
            adminIdInput.value = data.admin_id || '';
            botPrefixInput.value = data.prefix || '?';
            statBotName.innerText = data.bot_name || 'Zalo Bot';
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
        qrPlaceholder.classList.remove('hidden');
        qrImage.classList.add('hidden');
        qrStatusMsg.innerHTML = '<span class="badge badge-info">Generating</span> Đang tạo mã QR đăng nhập...';
        
        try {
            const res = await fetch('/api/qr/generate', { method: 'POST' });
            const data = await res.json();
            
            // Start polling QR status
            if (qrPollInterval) clearInterval(qrPollInterval);
            qrPollInterval = setInterval(pollQRStatus, 2000);
        } catch (err) {
            btnGenerateQr.disabled = false;
            qrStatusMsg.innerHTML = '<span class="badge badge-danger">Error</span> Lỗi kết nối server.';
        }
    }

    async function pollQRStatus() {
        try {
            const res = await fetch('/api/qr/status');
            const data = await res.json();
            
            if (data.status === 'generating') {
                qrStatusMsg.innerHTML = '<span class="badge badge-info">Generating</span> Đang tạo mã QR...';
            } else if (data.status === 'generated') {
                qrPlaceholder.classList.add('hidden');
                qrImage.src = data.image_path + '?t=' + new Date().getTime();
                qrImage.classList.remove('hidden');
                qrStatusMsg.innerHTML = '<span class="badge badge-info">Chờ Quét</span> Vui lòng dùng ứng dụng Zalo trên điện thoại quét mã QR để đăng nhập.';
                btnGenerateQr.disabled = false;
            } else if (data.status === 'success') {
                clearInterval(qrPollInterval);
                qrPollInterval = null;
                qrPlaceholder.classList.remove('hidden');
                qrImage.classList.add('hidden');
                qrPlaceholder.innerHTML = '<i class="fa-solid fa-circle-check" style="font-size: 3rem; color: #3fb950;"></i><p>Đăng nhập thành công!</p>';
                qrStatusMsg.innerHTML = `<span class="badge badge-success">Thành Công</span> Đã đăng nhập tài khoản: <strong>${data.user_info?.name || 'Zalo User'}</strong>`;
                appendTerminalLine(`[SYSTEM] Zalo login thành công! Tài khoản: ${data.user_info?.name}`, 'success');
                btnGenerateQr.disabled = false;
            } else if (data.status === 'failed') {
                clearInterval(qrPollInterval);
                qrPollInterval = null;
                qrPlaceholder.classList.remove('hidden');
                qrImage.classList.add('hidden');
                qrPlaceholder.innerHTML = '<i class="fa-solid fa-circle-xmark" style="font-size: 3rem; color: #f85149;"></i><p>Thất bại</p>';
                qrStatusMsg.innerHTML = `<span class="badge badge-danger">Lỗi</span> ${data.error_message}`;
                appendTerminalLine(`[SYSTEM ERROR] Đăng nhập QR thất bại: ${data.error_message}`, 'error');
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
            
            botRunning = data.running;
            
            // Update button states
            btnStartBot.disabled = botRunning;
            btnStopBot.disabled = !botRunning;
            
            // Update indicators
            if (botRunning) {
                sidebarStatusIndicator.classList.add('active');
                sidebarStatusText.innerText = 'Đang Chạy';
                sidebarStatusText.style.color = '#3fb950';
            } else {
                sidebarStatusIndicator.classList.remove('active');
                sidebarStatusText.innerText = 'Đang Dừng';
                sidebarStatusText.style.color = '#f85149';
            }
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
                        if (cleanLine.includes('[ERROR]') || cleanLine.includes('Lỗi') || cleanLine.includes('Exception')) {
                            type = 'error';
                        } else if (cleanLine.includes('[SYSTEM]') || cleanLine.includes('Khởi động')) {
                            type = 'system';
                        } else if (cleanLine.includes('thành công') || cleanLine.includes('SUCCESS') || cleanLine.includes('SẴN SÀNG')) {
                            type = 'success';
                        }
                        appendTerminalLine(cleanLine, type);
                    }
                });
            }
        } catch (err) {
            console.error('Error fetching logs:', err);
        }
    }
});
