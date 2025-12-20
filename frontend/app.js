/**
 * Candle Bias Dashboard - Frontend JavaScript
 * Fetches bias data and renders the dashboard
 */

// Configuration
const CONFIG = {
    // API_URL: 'http://localhost:8000', // Local development
    API_URL: '', // Will be set dynamically or use relative path for deployed version
    REFRESH_INTERVAL: 60000, // 1 minute auto-refresh (for display updates)
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
    // Try to detect API URL
    detectApiUrl();

    // Initialize theme
    initTheme();

    // Add event listeners
    elements.refreshBtn.addEventListener('click', handleRefresh);

    // Initial load: Try cache first for instant load
    loadFromCache();

    // Then fetch fresh data
    await fetchBiasData();

    // Set up auto-refresh
    setInterval(fetchBiasData, CONFIG.REFRESH_INTERVAL);
}

/**
 * Detect API URL based on environment
 */
function detectApiUrl() {
    // When deployed on Render, API is on same origin
    // When running locally via file://, use localhost
    if (window.location.protocol === 'file:') {
        CONFIG.API_URL = 'http://localhost:8000';
    } else {
        // For deployed version (Render), API is same origin
        CONFIG.API_URL = '';  // Empty = same origin
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

    // Only show full loading status if table is empty (no cache shown)
    // Check if we have data rows (excluding loading row)
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

        // Save to cache for next visit
        saveToCache(data);

        renderTable(data.data);
        updateStatus('online', 'Connected');
        elements.pairsCount.textContent = `${data.count} pairs`;

        lastUpdateTime = new Date();
        updateLastUpdateTime();

    } catch (error) {
        console.error('Error fetching data:', error);

        // If we have cached data shown, keep it visible
        if (elements.tableBody.querySelectorAll('tr').length > 1) {
            console.log('Keeping cached data visible despite fetch error');
            // Revert status to cached if we fail
            loadFromCache();
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
 * Render the bias table
 */
function renderTable(data) {
    if (!data || data.length === 0) {
        elements.tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="error-message">
                    <div class="error-icon">ðŸ“­</div>
                    <div>No data available</div>
                </td>
            </tr>
        `;
        return;
    }

    const rows = data.map(item => `
        <tr>
            <td class="symbol-cell">${escapeHtml(item.symbol)}</td>
            <td class="bias-cell">${renderBadge(item.daily)}</td>
            <td class="bias-cell">${renderBadge(item.weekly)}</td>
            <td class="bias-cell">${renderBadge(item.monthly)}</td>
            <td class="bias-cell">${renderSignalBadge(item.signal || 'WAIT')}</td>
        </tr>
    `).join('');

    elements.tableBody.innerHTML = rows;
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
    let icon = 'â¸ï¸'; // Pause icon for WAIT

    if (signal === 'BUY') {
        className = 'signal-buy';
        icon = 'ðŸŸ¢';
    } else if (signal === 'SELL') {
        className = 'signal-sell';
        icon = 'ðŸ”´';
    }

    return `<span class="badge ${className}">${icon} ${signal}</span>`;
}

/**
 * Format bias text for display (shorter on mobile)
 */
function formatBiasText(bias) {
    // Could shorten on mobile if needed
    return bias || 'NEUTRAL';
}

/**
 * Render error state
 */
function renderError(message) {
    elements.tableBody.innerHTML = `
        <tr>
            <td colspan="4" class="error-message">
                <div class="error-icon">âš ï¸</div>
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

    // Get saved theme or detect system preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const currentTheme = savedTheme || (systemPrefersDark ? 'dark' : 'light');

    // Apply theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);

    // Theme toggle event
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
    themeIcon.textContent = theme === 'dark' ? '??' : '??';
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
        // Auto-calculate on change
        ['mn1', 'w1', 'd1'].forEach(key => {
            if (this.dom[key]) {
                this.dom[key].addEventListener('change', () => this.calculate());
            }
        });

        // Settings toggle
        if (this.dom.toggleBtn) {
            this.dom.toggleBtn.addEventListener('click', () => {
                this.dom.settingsPanel.classList.toggle('hidden');
                const isHidden = this.dom.settingsPanel.classList.contains('hidden');
                this.dom.toggleBtn.textContent = isHidden ? 'âš™ï¸ Edit Rates' : 'âŒ Close';
            });
        }

        // Save settings
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
        // Normalize
        const m = mn1.toUpperCase();
        const w = w1.toUpperCase();
        const d = d1.toUpperCase();

        // Grade A+ Logic
        if ((m === 'STRONG BULL' && w === 'STRONG BULL' && d === 'BULL') ||
            (m === 'STRONG BEAR' && w === 'STRONG BEAR' && d === 'BEAR')) {
            return 'A+';
        }

        // Grade A Logic
        if ((m === 'STRONG BULL' && w === 'BULL' && d === 'BULL') ||
            (m === 'STRONG BEAR' && w === 'BEAR' && d === 'BEAR')) {
            return 'A';
        }

        // Grade A- Logic
        if ((m === 'BULL' && w === 'STRONG BULL' && d === 'BULL') ||
            (m === 'BEAR' && w === 'STRONG BEAR' && d === 'BEAR')) {
            return 'A-';
        }

        return 'B'; // Default/No Match
    },

    getWinRate(grade) {
        // Try localStorage first
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

        // Color coding
        this.dom.grade.className = 'grade-badge'; // reset
        if (grade.startsWith('A')) this.dom.grade.classList.add('grade-a');
        else if (grade === 'B') this.dom.grade.classList.add('grade-b');
    },

    loadSettings() {
        const rates = { ...this.defaults, ...this.getStoredRates() };

        // Populate inputs
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

        // Visual feedback
        const originalText = this.dom.saveBtn.textContent;
        this.dom.saveBtn.textContent = 'âœ… Saved!';
        setTimeout(() => {
            this.dom.saveBtn.textContent = originalText;
            this.dom.settingsPanel.classList.add('hidden');
            this.dom.toggleBtn.textContent = 'âš™ï¸ Edit Rates';
        }, 1000);

        // Recalculate to show new values immediately
        this.calculate();
    }
};

// Initialize Calculator when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    Calculator.init();
});

