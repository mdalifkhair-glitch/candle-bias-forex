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

    // Initial data fetch
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
    updateStatus('loading', 'Fetching data...');

    try {
        const response = await fetch(`${CONFIG.API_URL}/api/bias`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        renderTable(data.data);
        updateStatus('online', 'Connected');
        elements.pairsCount.textContent = `${data.count} pairs`;

        lastUpdateTime = new Date();
        updateLastUpdateTime();

    } catch (error) {
        console.error('Error fetching data:', error);
        updateStatus('error', 'Connection failed');
        renderError(error.message);
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
                <td colspan="4" class="error-message">
                    <div class="error-icon">📭</div>
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
// Social Sharing Functions
// ====================================

function shareTwitter() {
    const text = 'Check out this Forex Bias Dashboard - Multi-timeframe trend analysis!';
    const url = window.location.href;
    window.open(
        `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`,
        '_blank',
        'width=550,height=420'
    );
}

function shareFacebook() {
    const url = window.location.href;
    window.open(
        `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
        '_blank',
        'width=550,height=420'
    );
}

function shareWhatsApp() {
    const text = 'Check out this Forex Bias Dashboard: ' + window.location.href;
    window.open(
        `https://wa.me/?text=${encodeURIComponent(text)}`,
        '_blank'
    );
}

function copyLink() {
    navigator.clipboard.writeText(window.location.href).then(() => {
        // Show success feedback
        const btn = event.target.closest('.share-btn');
        const originalText = btn.textContent;
        btn.textContent = '? Copied!';
        btn.style.backgroundColor = '#10b981';
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.backgroundColor = '';
        }, 2000);
    }).catch(err => {
        alert('Link: ' + window.location.href);
    });
}
