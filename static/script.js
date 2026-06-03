function generatePassword(length = 16) {
    const lower = 'abcdefghijklmnopqrstuvwxyz';
    const upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const digits = '0123456789';
    const symbols = '!@#$%^&*()-_=+[]{};:,.<>?';
    const all = lower + upper + digits + symbols;
    let pw = '';
    pw += lower[Math.floor(Math.random() * lower.length)];
    pw += upper[Math.floor(Math.random() * upper.length)];
    pw += digits[Math.floor(Math.random() * digits.length)];
    pw += symbols[Math.floor(Math.random() * symbols.length)];
    for (let i = pw.length; i < length; i++) {
        pw += all[Math.floor(Math.random() * all.length)];
    }
    return pw.split('').sort(() => 0.5 - Math.random()).join('');
}

document.addEventListener('DOMContentLoaded', () => {
    const generateButton = document.getElementById('generatePassword');
    if (generateButton) {
        generateButton.addEventListener('click', () => {
            const input = document.getElementById('password');
            if (!input) return;
            const pwd = generatePassword(16);
            input.value = pwd;
            input.type = 'text';
            setTimeout(() => { input.type = 'password'; }, 5000);
            updateStrengthDisplay(pwd);
        });
    }

    document.querySelectorAll('.btn-copy').forEach((button) => {
        button.addEventListener('click', (event) => {
            const row = event.target.closest('tr');
            if (!row) return;
            const pwdEl = row.querySelector('[data-password]');
            const pwd = pwdEl ? pwdEl.getAttribute('data-password') : '';
            if (!pwd) return;
            copyTextToClipboard(pwd).then(() => {
                button.textContent = 'Đã sao chép';
                setTimeout(() => { button.textContent = 'Sao chép'; }, 2000);
            }).catch(() => {
                button.textContent = 'Không copy được';
                setTimeout(() => { button.textContent = 'Sao chép'; }, 2000);
            });
        });
    });

    document.querySelectorAll('.btn-toggle').forEach((button) => {
        button.addEventListener('click', (event) => {
            const row = event.target.closest('tr');
            if (!row) return;
            const pwdEl = row.querySelector('[data-password]');
            if (!pwdEl) return;
            const isHidden = pwdEl.getAttribute('data-hidden') === 'true';
            if (isHidden) {
                pwdEl.textContent = pwdEl.getAttribute('data-password');
                pwdEl.setAttribute('data-hidden', 'false');
                button.textContent = 'Ẩn';
            } else {
                const hidden = '•'.repeat(Math.max(8, pwdEl.getAttribute('data-password').length));
                pwdEl.textContent = hidden;
                pwdEl.setAttribute('data-hidden', 'true');
                button.textContent = 'Hiện';
            }
        });
    });

    const pwdInput = document.getElementById('password');
    if (pwdInput) {
        pwdInput.addEventListener('input', (event) => {
            updateStrengthDisplay(event.target.value);
        });
        updateStrengthDisplay(pwdInput.value || '');
    }
});

function copyTextToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        return navigator.clipboard.writeText(text);
    }
    return new Promise((resolve, reject) => {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        try {
            const successful = document.execCommand('copy');
            document.body.removeChild(textarea);
            if (successful) {
                resolve();
            } else {
                reject(new Error('copy failed'));
            }
        } catch (err) {
            document.body.removeChild(textarea);
            reject(err);
        }
    });
}

function updateStrengthDisplay(password) {
    const strengthEl = document.getElementById('passwordStrength');
    if (!strengthEl) return;
    const result = evaluateStrength(password);
    strengthEl.textContent = result.label;
    strengthEl.className = 'password-strength ' + result.css;
}

function evaluateStrength(password) {
    if (!password) return { label: 'Chưa có', css: 'strength-neutral' };
    const hasLower = /[a-z]/.test(password);
    const hasUpper = /[A-Z]/.test(password);
    const hasDigit = /[0-9]/.test(password);
    const hasSym = /[^A-Za-z0-9]/.test(password);
    const length = password.length;
    const categories = [hasLower, hasUpper, hasDigit, hasSym].filter(Boolean).length;
    if (length >= 12 && categories >= 3) return { label: 'Mạnh', css: 'strength-strong' };
    if (length >= 8 && categories >= 2) return { label: 'Trung bình', css: 'strength-medium' };
    return { label: 'Yếu', css: 'strength-weak' };
}
