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
    let authMode = 'login'; // login or register
    
    // Auth DOM Elements
    const authOverlay = document.getElementById('auth-overlay');
    const mainAppContainer = document.getElementById('main-app-container');
    const authForm = document.getElementById('auth-form');
    const authUsernameInput = document.getElementById('auth-username');
    const authPasswordInput = document.getElementById('auth-password');
    const btnAuthSubmit = document.getElementById('btn-auth-submit');
    const authTitle = document.getElementById('auth-title');
    const authSubtitle = document.getElementById('auth-subtitle');
    const authToggleLink = document.getElementById('auth-toggle-link');
    const authToggleText = document.getElementById('auth-toggle-text');
    const authErrorMsg = document.getElementById('auth-error-msg');
    const userDisplayName = document.getElementById('user-display-name');
    const btnLogout = document.getElementById('btn-logout');
    
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
        'cv2': 'opencv-python',
        'audioop': 'audioop-lts'
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
    checkSession();
    initGoogleSignIn();

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

    authToggleLink.addEventListener('click', toggleAuthMode);
    authForm.addEventListener('submit', handleAuthSubmit);
    btnLogout.addEventListener('click', handleLogout);

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

    // ============================
    // AUTHENTICATION LOGIC
    // ============================

    // Google Sign-In handler (called by Google GSI)
    window.handleGoogleSignIn = async function(response) {
        const credential = response.credential;
        try {
            const res = await fetch('/api/auth/google', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ credential })
            });
            const data = await res.json();
            if (data.status === 'success') {
                checkSession();
            } else {
                showAuthError(data.message);
            }
        } catch (err) {
            showAuthError('Lỗi kết nối Google: ' + err.message);
        }
    };

    async function initGoogleSignIn() {
        try {
            const res = await fetch('/api/auth/config');
            const config = await res.json();
            const clientId = config.google_client_id;
            
            if (!clientId) return; // Google login not configured - hide button
            
            // Show Google button and divider
            document.getElementById('google-signin-container').classList.remove('hidden');
            document.getElementById('auth-divider').classList.remove('hidden');
            document.getElementById('auth-divider').style.display = 'flex';
            
            // Dynamically load Google Identity Services script
            const script = document.createElement('script');
            script.src = 'https://accounts.google.com/gsi/client';
            script.async = true;
            script.defer = true;
            script.onload = () => {
                google.accounts.id.initialize({
                    client_id: clientId,
                    callback: window.handleGoogleSignIn,
                    auto_select: false,
                    cancel_on_tap_outside: true,
                });
                google.accounts.id.renderButton(
                    document.getElementById('google-signin-btn'),
                    {
                        theme: 'filled_blue',
                        size: 'large',
                        shape: 'rectangular',
                        text: 'signin_with',
                        width: 300,
                        logo_alignment: 'left',
                    }
                );
            };
            document.head.appendChild(script);
        } catch (err) {
            console.error('Google Sign-In init error:', err);
        }
    }

    async function checkSession() {
        try {
            const res = await fetch('/api/auth/session');
            const data = await res.json();
            if (data.logged_in) {
                userDisplayName.innerText = data.username;
                authOverlay.classList.add('hidden');
                mainAppContainer.classList.remove('hidden');
                
                // Load user config and start monitoring
                loadConfig();
                checkBotStatus();
                if (!statusPollInterval) statusPollInterval = setInterval(checkBotStatus, 3000);
                if (!logsPollInterval) logsPollInterval = setInterval(fetchLogs, 1500);
            } else {
                showAuthForm();
            }
        } catch (err) {
            console.error('Lỗi check session:', err);
            showAuthForm();
        }
    }

    function showAuthForm() {
        authOverlay.classList.remove('hidden');
        mainAppContainer.classList.add('hidden');
        
        // Stop all intervals
        if (statusPollInterval) { clearInterval(statusPollInterval); statusPollInterval = null; }
        if (logsPollInterval) { clearInterval(logsPollInterval); logsPollInterval = null; }
        if (qrPollInterval) { clearInterval(qrPollInterval); qrPollInterval = null; }
    }

    function toggleAuthMode(e) {
        e.preventDefault();
        authErrorMsg.classList.add('hidden');
        authUsernameInput.value = '';
        authPasswordInput.value = '';
        
        if (authMode === 'login') {
            authMode = 'register';
            authTitle.innerText = 'Đăng Ký ZaloBot';
            authSubtitle.innerText = 'Tạo tài khoản quản lý bot Zalo của riêng bạn';
            btnAuthSubmit.innerText = 'Đăng Ký';
            authToggleText.innerText = 'Đã có tài khoản?';
            authToggleLink.innerText = 'Đăng nhập ngay';
        } else {
            authMode = 'login';
            authTitle.innerText = 'Đăng Nhập ZaloBot';
            authSubtitle.innerText = 'Quản lý phiên Zalo Bot riêng tư của bạn';
            btnAuthSubmit.innerText = 'Đăng Nhập';
            authToggleText.innerText = 'Chưa có tài khoản?';
            authToggleLink.innerText = 'Đăng ký ngay';
        }
    }

    async function handleAuthSubmit(e) {
        e.preventDefault();
        authErrorMsg.classList.add('hidden');
        btnAuthSubmit.disabled = true;
        
        const username = authUsernameInput.value.trim();
        const password = authPasswordInput.value;
        
        const endpoint = authMode === 'login' ? '/api/auth/login' : '/api/auth/register';
        
        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            
            if (data.status === 'success') {
                if (authMode === 'register') {
                    // Registration success - switch to login and show success message
                    authMode = 'login';
                    authTitle.innerText = 'Đăng Nhập ZaloBot';
                    authSubtitle.innerText = 'Quản lý phiên Zalo Bot riêng tư của bạn';
                    btnAuthSubmit.innerText = 'Đăng Nhập';
                    authToggleText.innerText = 'Chưa có tài khoản?';
                    authToggleLink.innerText = 'Đăng ký ngay';
                    
                    authErrorMsg.innerText = data.message;
                    authErrorMsg.style.backgroundColor = 'rgba(63, 185, 80, 0.15)';
                    authErrorMsg.style.borderColor = 'rgba(63, 185, 80, 0.25)';
                    authErrorMsg.style.color = '#3fb950';
                    authErrorMsg.classList.remove('hidden');
                    
                    authUsernameInput.value = username;
                    authPasswordInput.value = '';
                } else {
                    // Login success
                    checkSession();
                }
            } else {
                showAuthError(data.message);
            }
        } catch (err) {
            showAuthError('Lỗi kết nối đến server: ' + err.message);
        } finally {
            btnAuthSubmit.disabled = false;
        }
    }

    function showAuthError(msg) {
        authErrorMsg.innerText = msg;
        authErrorMsg.style.backgroundColor = 'rgba(248, 81, 73, 0.15)';
        authErrorMsg.style.borderColor = 'rgba(248, 81, 73, 0.25)';
        authErrorMsg.style.color = '#ff6b6b';
        authErrorMsg.classList.remove('hidden');
    }

    async function handleLogout(e) {
        e.preventDefault();
        try {
            const res = await fetch('/api/auth/logout', { method: 'POST' });
            const data = await res.json();
            if (data.status === 'success') {
                showAuthForm();
                // Clear UI fields
                botNameInput.value = '';
                adminIdInput.value = '';
                botPrefixInput.value = '';
                statBotName.innerText = '-';
                if (mobileBotName) mobileBotName.innerText = '-';
                
                qrPlaceholder.innerHTML = '<i class="fa-solid fa-qrcode" style="font-size: 2.5rem; opacity: 0.3;"></i><p>Nhấn nút bên dưới để lấy mã QR</p>';
                qrPlaceholder.classList.remove('hidden');
                qrImage.classList.add('hidden');
                qrStatusMsg.innerHTML = '<span class="badge badge-info">Idle</span> Nhấn nút để lấy mã QR đăng nhập';
                
                terminalBody.innerHTML = '<div class="terminal-line system-line">[SYSTEM] Sẵn sàng điều khiển. Chờ lệnh từ bảng điều khiển...</div>';
            }
        } catch (err) {
            console.error('Logout error:', err);
        }
    }
});
