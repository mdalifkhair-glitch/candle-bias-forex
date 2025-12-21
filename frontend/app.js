/**
 * Candle Bias Dashboard - Frontend JavaScript (FIXED)
 * Missing functions added: cache, share, and signal styling
 */

// Configuration
const CONFIG = {
    API_URL: '',
    REFRESH_INTERVAL: 60000,
    CACHE_KEY: 'biasData',
    CACHE_TIMESTAMP_KEY: 'biasDataTimestamp',
    CACHE_EXPIRY: 300000 // 5 minutes
};

// State
let isLoading = false;
let lastUpdateTime = null;

// DOM Elements
const elements = {
    tableBody: document.getElementById('biasTableBody'),
    refreshBtn: document.getElementById('refreshBtn'),
    lastUpdate: document.getElementById('lastUpdate'),
    statusDot: document.getElementById('statusDot'),
    statusText: document.getElementById('statusText'),
    pairsCount: document.getElementById('pairsCount'),
};

/**
 * Initialize the dashboard
 */
async function init() {
    detectApiUrl();
    initTheme();
    elements.refreshBtn.addEventListener('click', handleRefresh);
    
    // Load cache first for instant display
    loadFromCache();
    
    // Fetch fresh data
    await fetchBiasData();
    
    // Auto-refresh
    setInterval(fetchBiasData, CONFIG.REFRESH_INTERVAL);
}

/**
 * Detect API URL based on environment
 */
function detectApiUrl() {
    if (window.location.protocol === 'file:') {
        CONFIG.API_URL = 'http://localhost:8000';
    } else {
        CONFIG.API_URL = '';
    }
}

/**
 * Handle refresh button click
 */
async function handleRefresh() {
    if (isLoading) return;
    await fetchBiasData();
}

/**
 * Fetch bias data from API
 */
async function fetchBiasData() {
    if (isLoading) return;

    isLoading = true;
    elements.refreshBtn.classList.add('loading');

    const hasData = elements.tableBody.querySelectorAll('tr').length > 1;

    if (!hasData) {
        updateStatus('loading', 'Fetching data...');
    } else {
        updateStatus('loading', 'Updating...');
    }

    try {
        const apiUrl = `${CONFIG.API_URL}/api/bias`;
        console.log('Fetching from:', apiUrl);

        const response = await fetch(apiUrl);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Save to cache
        saveToCache(data);

        renderTable(data.data);
        updateStatus('online', 'Connected');
        elements.pairsCount.textContent = `${data.count} pairs`;

        lastUpdateTime = new Date();
        updateLastUpdateTime();

    } catch (error) {
        console.error('Error fetching data:', error);

        if (elements.tableBody.querySelectorAll('tr').length > 1) {
            console.log('Keeping cached data visible');
            updateStatus('cached', 'Using cached data');
        } else {
            updateStatus('error', 'Connection failed');
            renderError(error.message);
        }
    } finally {
        isLoading = false;
        elements.refreshBtn.classList.remove('loading');
    }
}

/**
 * Save data to localStorage cache
 */
function saveToCache(data) {
    try {
        localStorage.setItem(CONFIG.CACHE_KEY, JSON.stringify(data));
        localStorage.setItem(CONFIG.CACHE_TIMESTAMP_KEY, Date.now().toString());
        console.log('Data cached successfully');
    } catch (error) {
        console.error('Cache save failed:', error);
    }
}

/**
 * Load data from localStorage cache
 */
function loadFromCache() {
    try {
        const cachedData = localStorage.getItem(CONFIG.CACHE_KEY);
        const cacheTimestamp = localStorage.getItem(CONFIG.CACHE_TIMESTAMP_KEY);
        
        if (!cachedData || !cacheTimestamp) {
            console.log('No cache available');
            return;
        }

        const age = Date.now() - parseInt(cacheTimestamp);
        const data = JSON.parse(cachedData);

        if (age > CONFIG.CACHE_EXPIRY) {
            console.log('Cache expired');
            return;
        }

        console.log('Loading from cache');
        renderTable(data.data);
        updateStatus('cached', 'Cached data');
        elements.pairsCount.textContent = `${data.count} pairs`;
        
        lastUpdateTime = new Date(parseInt(cacheTimestamp));
        updateLastUpdateTime();

    } catch (error) {
        console.error('Cache load failed:', error);
    }
}

/**
 * Render the bias table with signal styling
 */
function renderTable(data) {
    if (!data || data.length === 0) {
        elements.tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="error-message">
                    <div class="error-icon">🔭</div>
                    <div>No data available</div>
                </td>
            </tr>
        `;
        return;
    }

    const rows = data.map(item => {
        const signal = item.signal || 'WAIT';
        const rowClass = getSignalRowClass(signal);
        
        return `
            <tr class="${rowClass}">
                <td class="symbol-cell">${escapeHtml(item.symbol)}</td>
                <td class="bias-cell">${renderBadge(item.daily)}</td>
                <td class="bias-cell">${renderBadge(item.weekly)}</td>
                <td class="bias-cell">${renderBadge(item.monthly)}</td>
                <td class="bias-cell">${renderSignalBadge(signal)}</td>
            </tr>
        `;
    }).join('');

    elements.tableBody.innerHTML = rows;
}

/**
 * Get CSS class for signal row styling
 */
function getSignalRowClass(signal) {
    const classMap = {
        'BUY': 'signal-buy-row',
        'SELL': 'signal-sell-row',
        'WAIT': 'signal-wait-row'
    };
    return classMap[signal] || 'signal-wait-row';
}

/**
 * Render a bias badge
 */
function renderBadge(bias) {
    const biasClass = getBiasClass(bias);
    const displayText = formatBiasText(bias);
    return `<span class="badge ${biasClass}">${displayText}</span>`;
}

/**
 * Get CSS class for bias
 */
function getBiasClass(bias) {
    const classMap = {
        'STRONG BULL': 'strong-bull',
        'BULL': 'bull',
        'NEUTRAL': 'neutral',
        'BEAR': 'bear',
        'STRONG BEAR': 'strong-bear',
    };
    return classMap[bias] || 'neutral';
}

/**
 * Render a signal badge
 */
function renderSignalBadge(signal) {
    let className = 'signal-wait';
    let icon = '⏸️';

    if (signal === 'BUY') {
        className = 'signal-buy';
        icon = '🟢';
    } else if (signal === 'SELL') {
        className = 'signal-sell';
        icon = '🔴';
    }

    return `<span class="badge ${className}">${icon} ${signal}</span>`;
}

/**
 * Format bias text for display
 */
function formatBiasText(bias) {
    return bias || 'NEUTRAL';
}

/**
 * Render error state
 */
function renderError(message) {
    elements.tableBody.innerHTML = `
        <tr>
            <td colspan="5" class="error-message">
                <div class="error-icon">⚠️</div>
                <div>Failed to load data</div>
                <div style="font-size: 0.75rem; margin-top: 8px;">${escapeHtml(message)}</div>
                <div style="font-size: 0.7rem; margin-top: 4px; color: #718096;">
                    Make sure the backend server is running
                </div>
            </td>
        </tr>
    `;
}

/**
 * Update status indicator
 */
function updateStatus(status, text) {
    elements.statusDot.className = 'status-dot ' + status;
    elements.statusText.textContent = text;
}

/**
 * Update last update time display
 */
function updateLastUpdateTime() {
    if (!lastUpdateTime) {
        elements.lastUpdate.textContent = '--';
        return;
    }

    const now = new Date();
    const diff = Math.floor((now - lastUpdateTime) / 1000);

    if (diff < 60) {
        elements.lastUpdate.textContent = 'Just now';
    } else if (diff < 3600) {
        const mins = Math.floor(diff / 60);
        elements.lastUpdate.textContent = `${mins}m ago`;
    } else {
        elements.lastUpdate.textContent = lastUpdateTime.toLocaleTimeString();
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Update time display every minute
setInterval(updateLastUpdateTime, 60000);

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', init);

// ====================================
// Theme Toggle
// ====================================

function initTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');

    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const currentTheme = savedTheme || (systemPrefersDark ? 'dark' : 'light');

    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);

    themeToggle.addEventListener('click', () => {
        const theme = document.documentElement.getAttribute('data-theme');
        const newTheme = theme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });
}

function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('themeIcon');
    themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// ====================================
// Share Functions
// ====================================

function shareTwitter() {
    const text = encodeURIComponent('Check out Market Bias Pro - Multi-timeframe Forex trend analysis dashboard!');
    const url = encodeURIComponent(window.location.href);
    window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, '_blank');
}

function shareFacebook() {
    const url = encodeURIComponent(window.location.href);
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank');
}

function shareWhatsApp() {
    const text = encodeURIComponent('Check out Market Bias Pro - Multi-timeframe Forex trend analysis dashboard! ' + window.location.href);
    window.open(`https://wa.me/?text=${text}`, '_blank');
}

function copyLink() {
    navigator.clipboard.writeText(window.location.href).then(() => {
        alert('Link copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy link');
    });
}

// ====================================
// Win % Calculator Module
// ====================================

const Calculator = {
    defaults: {
        'A+': 90,
        'A': 80,
        'A-': 70,
        'B': 50
    },

    init() {
        this.cacheDom();
        this.bindEvents();
        this.loadSettings();
    },

    cacheDom() {
        this.dom = {
            mn1: document.getElementById('calcMn1'),
            w1: document.getElementById('calcW1'),
            d1: document.getElementById('calcD1'),
            grade: document.getElementById('calcGrade'),
            winRate: document.getElementById('calcWinRate'),
            toggleBtn: document.getElementById('toggleSettingsBtn'),
            settingsPanel: document.getElementById('calcSettings'),
            saveBtn: document.getElementById('saveRatesBtn'),
            inputs: {
                'A+': document.getElementById('rateAPlus'),
                'A': document.getElementById('rateA'),
                'A-': document.getElementById('rateAMinus'),
                'B': document.getElementById('rateB')
            }
        };
    },

    bindEvents() {
        ['mn1', 'w1', 'd1'].forEach(key => {
            if (this.dom[key]) {
                this.dom[key].addEventListener('change', () => this.calculate());
            }
        });

        if (this.dom.toggleBtn) {
            this.dom.toggleBtn.addEventListener('click', () => {
                this.dom.settingsPanel.classList.toggle('hidden');
                const isHidden = this.dom.settingsPanel.classList.contains('hidden');
                this.dom.toggleBtn.textContent = isHidden ? '⚙️ Edit Rates' : '❌ Close';
            });
        }

        if (this.dom.saveBtn) {
            this.dom.saveBtn.addEventListener('click', () => this.saveSettings());
        }
    },

    calculate() {
        const mn1 = this.dom.mn1.value;
        const w1 = this.dom.w1.value;
        const d1 = this.dom.d1.value;

        if (!mn1 || !w1 || !d1) {
            this.updateUI('--', '--%');
            return;
        }

        const grade = this.determineGrade(mn1, w1, d1);
        const winRate = this.getWinRate(grade);

        this.updateUI(grade, winRate ? `${winRate}%` : 'N/A');
    },

    determineGrade(mn1, w1, d1) {
        const m = mn1.toUpperCase();
        const w = w1.toUpperCase();
        const d = d1.toUpperCase();

        if ((m === 'STRONG BULL' && w === 'STRONG BULL' && d === 'BULL') ||
            (m === 'STRONG BEAR' && w === 'STRONG BEAR' && d === 'BEAR')) {
            return 'A+';
        }

        if ((m === 'STRONG BULL' && w === 'BULL' && d === 'BULL') ||
            (m === 'STRONG BEAR' && w === 'BEAR' && d === 'BEAR')) {
            return 'A';
        }

        if ((m === 'BULL' && w === 'STRONG BULL' && d === 'BULL') ||
            (m === 'BEAR' && w === 'STRONG BEAR' && d === 'BEAR')) {
            return 'A-';
        }

        return 'B';
    },

    getWinRate(grade) {
        const savedRates = this.getStoredRates();
        return savedRates[grade] || this.defaults[grade] || 0;
    },

    getStoredRates() {
        try {
            return JSON.parse(localStorage.getItem('calcWinRates')) || {};
        } catch {
            return {};
        }
    },

    updateUI(grade, winRate) {
        this.dom.grade.textContent = grade;
        this.dom.winRate.textContent = winRate;

        this.dom.grade.className = 'grade-badge';
        if (grade.startsWith('A')) this.dom.grade.classList.add('grade-a');
        else if (grade === 'B') this.dom.grade.classList.add('grade-b');
    },

    loadSettings() {
        const rates = { ...this.defaults, ...this.getStoredRates() };

        for (const [grade, value] of Object.entries(rates)) {
            if (this.dom.inputs[grade]) {
                this.dom.inputs[grade].value = value;
            }
        }
    },

    saveSettings() {
        const newRates = {
            'A+': this.dom.inputs['A+'].value,
            'A': this.dom.inputs['A'].value,
            'A-': this.dom.inputs['A-'].value,
            'B': this.dom.inputs['B'].value
        };

        localStorage.setItem('calcWinRates', JSON.stringify(newRates));

        const originalText = this.dom.saveBtn.textContent;
        this.dom.saveBtn.textContent = '✅ Saved!';
        setTimeout(() => {
            this.dom.saveBtn.textContent = originalText;
            this.dom.settingsPanel.classList.add('hidden');
            this.dom.toggleBtn.textContent = '⚙️ Edit Rates';
        }, 1000);

        this.calculate();
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Calculator.init();
});