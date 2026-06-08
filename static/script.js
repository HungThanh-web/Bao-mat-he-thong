const PASSWORD_SETS = {
    lower: 'abcdefghijklmnopqrstuvwxyz',
    upper: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    digits: '0123456789',
    symbols: '!@#$%^&*()-_=+[]{};:,.<>?'
};

function secureRandomInt(max) {
    const values = new Uint32Array(1);
    crypto.getRandomValues(values);
    return values[0] % max;
}

function shuffleChars(chars) {
    const copy = [...chars];
    for (let i = copy.length - 1; i > 0; i -= 1) {
        const j = secureRandomInt(i + 1);
        [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy.join('');
}

function generatePasswordFromOptions() {
    const lengthInput = document.getElementById('passwordLength');
    const length = Math.min(64, Math.max(8, Number(lengthInput?.value || 20)));
    const enabledSets = [
        document.getElementById('useLower')?.checked ? PASSWORD_SETS.lower : '',
        document.getElementById('useUpper')?.checked ? PASSWORD_SETS.upper : '',
        document.getElementById('useDigits')?.checked ? PASSWORD_SETS.digits : '',
        document.getElementById('useSymbols')?.checked ? PASSWORD_SETS.symbols : ''
    ].filter(Boolean);

    if (!enabledSets.length) {
        enabledSets.push(PASSWORD_SETS.lower, PASSWORD_SETS.upper, PASSWORD_SETS.digits, PASSWORD_SETS.symbols);
    }

    const all = enabledSets.join('');
    let password = enabledSets.map((set) => set[secureRandomInt(set.length)]).join('');
    while (password.length < length) {
        password += all[secureRandomInt(all.length)];
    }
    return shuffleChars(password);
}

document.addEventListener('DOMContentLoaded', () => {
    wirePasswordGenerator();
    wireVaultActions();
    wireAutoLock();
    wireVisibilityShield();

    const pwdInput = document.getElementById('password');
    if (pwdInput) {
        pwdInput.addEventListener('input', (event) => updateStrengthDisplay(event.target.value));
        updateStrengthDisplay(pwdInput.value || '');
    }
});

function wirePasswordGenerator() {
    const generateButton = document.getElementById('generatePassword');
    if (!generateButton) return;

    generateButton.addEventListener('click', () => {
        const input = document.getElementById('password');
        if (!input) return;
        const pwd = generatePasswordFromOptions();
        input.value = pwd;
        input.type = 'text';
        updateStrengthDisplay(pwd);
        setTimeout(() => {
            if (input.value === pwd) input.type = 'password';
        }, 5000);
    });
}

function wireVaultActions() {
    document.querySelectorAll('.btn-copy').forEach((button) => {
        button.addEventListener('click', (event) => {
            const pwd = getPasswordFromRow(event.target);
            if (!pwd) return;
            copyTextToClipboard(pwd).then(() => {
                button.textContent = 'Đã sao chép';
                setTimeout(() => { button.textContent = 'Sao chép'; }, 2000);
                setTimeout(() => {
                    navigator.clipboard?.writeText('').catch(() => {});
                }, 60000);
            }).catch(() => {
                button.textContent = 'Không copy được';
                setTimeout(() => { button.textContent = 'Sao chép'; }, 2000);
            });
        });
    });

    document.querySelectorAll('.btn-toggle').forEach((button) => {
        button.addEventListener('click', (event) => {
            const row = event.target.closest('tr');
            const pwdEl = row?.querySelector('[data-password]');
            if (!pwdEl) return;
            const isHidden = pwdEl.getAttribute('data-hidden') === 'true';
            if (isHidden) {
                pwdEl.textContent = pwdEl.getAttribute('data-password');
                pwdEl.setAttribute('data-hidden', 'false');
                button.textContent = 'Ẩn';
            } else {
                hideSecret(pwdEl);
                button.textContent = 'Hiện';
            }
        });
    });
}

function getPasswordFromRow(target) {
    const row = target.closest('tr');
    const pwdEl = row?.querySelector('[data-password]');
    return pwdEl?.getAttribute('data-password') || '';
}

function hideSecret(element) {
    const length = Math.max(8, element.getAttribute('data-password')?.length || 8);
    element.textContent = '•'.repeat(length);
    element.setAttribute('data-hidden', 'true');
}

function copyTextToClipboard(text) {
    if (navigator.clipboard?.writeText) {
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
            successful ? resolve() : reject(new Error('copy failed'));
        } catch (err) {
            document.body.removeChild(textarea);
            reject(err);
        }
    });
}

function wireAutoLock() {
    if (document.body.dataset.authenticated !== 'true') return;
    const lockSeconds = Number(document.body.dataset.lockSeconds || 300);
    let timerId;
    const resetTimer = () => {
        window.clearTimeout(timerId);
        timerId = window.setTimeout(() => {
            window.location.href = '/logout';
        }, lockSeconds * 1000);
    };
    ['click', 'keydown', 'mousemove', 'scroll', 'touchstart'].forEach((eventName) => {
        document.addEventListener(eventName, resetTimer, { passive: true });
    });
    resetTimer();
}

function wireVisibilityShield() {
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            document.querySelectorAll('[data-password]').forEach(hideSecret);
            document.querySelectorAll('.btn-toggle').forEach((button) => {
                button.textContent = 'Hiện';
            });
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
    const categories = [hasLower, hasUpper, hasDigit, hasSym].filter(Boolean).length;
    if (password.length >= 14 && categories >= 4) return { label: 'Mạnh', css: 'strength-strong' };
    if (password.length >= 10 && categories >= 3) return { label: 'Trung bình', css: 'strength-medium' };
    return { label: 'Yếu', css: 'strength-weak' };
}
