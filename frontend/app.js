/**
 * Market Bias Pro - Enhanced with Signal Priority Layout
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
let selectedMarket = 'forex';
let selectedStyle = 'position';
let selectedTimeframes = { tf1: 'monthly', tf2: 'weekly', tf3: 'daily' };

// DOM Elements
const elements = {
    refreshBtn: document.getElementById('refreshBtn'),
    lastUpdate: document.getElementById('lastUpdate'),
    statusDot: document.getElementById('statusDot'),
    statusText: document.getElementById('statusText'),
    pairsCount: document.getElementById('pairsCount'),
    
    // Signal sections
    buyTableBody: document.getElementById('buyTableBody'),
    sellTableBody: document.getElementById('sellTableBody'),
    noSignalTableBody: document.getElementById('noSignalTableBody'),
    
    buyCount: document.getElementById('buyCount'),
    sellCount: document.getElementById('sellCount'),
    noSignalCount: document.getElementById('noSignalCount'),
    
    // Headers
    buyHeader1: document.getElementById('buyHeader1'),
    buyHeader2: document.getElementById('buyHeader2'),
    buyHeader3: document.getElementById('buyHeader3'),
    sellHeader1: document.getElementById('sellHeader1'),
    sellHeader2: document.getElementById('sellHeader2'),
    sellHeader3: document.getElementById('sellHeader3'),
    noSignalHeader1: document.getElementById('noSignalHeader1'),
    noSignalHeader2: document.getElementById('noSignalHeader2'),
    noSignalHeader3: document.getElementById('noSignalHeader3'),
};

/**
 * Initialize the dashboard
 */
async function init() {
    detectApiUrl();
    initTheme();
    initMarketButtons();
    initStyleButtons();
    elements.refreshBtn.addEventListener('click', handleRefresh);
    
    // Load cache first
    loadFromCache();
    
    // Fetch fresh data
    await fetchBiasData();
    
    // Auto-refresh
    setInterval(fetchBiasData, CONFIG.REFRESH_INTERVAL);
    
    // Set initial max-height for collapsible sections
    document.querySelectorAll('.section-content').forEach(content => {
        content.style.maxHeight = content.scrollHeight + 'px';
    });
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
 * Initialize market type buttons
 */
function initMarketButtons() {
    document.querySelectorAll('.market-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.market-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            selectedMarket = this.dataset.market;
            fetchBiasData();
        });
    });
}

/**
 * Initialize trading style buttons
 */
function initStyleButtons() {
    document.querySelectorAll('.style-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.style-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            selectedStyle = this.dataset.style;
            selectedTimeframes = {
                tf1: this.dataset.tf1,
                tf2: this.dataset.tf2,
                tf3: this.dataset.tf3
            };
            updateTableHeaders();
            fetchBiasData();
        });
    });
}

/**
 * Update table headers based on selected timeframes
 */
function updateTableHeaders() {
    const headerMap = {
        'monthly': 'MONTHLY',
        'weekly': 'WEEKLY',
        'daily': 'DAILY',
        'h4': '4-HOUR',
        'h1': '1-HOUR',
        'm15': '15-MIN'
    };
    
    const header1 = headerMap[selectedTimeframes.tf1] || 'TF1';
    const header2 = headerMap[selectedTimeframes.tf2] || 'TF2';
    const header3 = headerMap[selectedTimeframes.tf3] || 'TF3';
    
    // Update all section headers
    [elements.buyHeader1, elements.sellHeader1, elements.noSignalHeader1].forEach(el => el.textContent = header1);
    [elements.buyHeader2, elements.sellHeader2, elements.noSignalHeader2].forEach(el => el.textContent = header2);
    [elements.buyHeader3, elements.sellHeader3, elements.noSignalHeader3].forEach(el => el.textContent = header3);
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
        const apiUrl = `${CONFIG.API_URL}/api/bias`;
        console.log('Fetching from:', apiUrl);

        const response = await fetch(apiUrl);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Save to cache
        saveToCache(data);

        // Render data in signal sections
        renderSignalSections(data.data);
        
        updateStatus('online', 'Connected');
        elements.pairsCount.textContent = `${data.count} pairs`;

        lastUpdateTime = new Date();
        updateLastUpdateTime();

    } catch (error) {
        console.error('Error fetching data:', error);
        updateStatus('error', 'Connection failed');
        
        // Keep cached data visible if available
        if (elements.buyTableBody.querySelectorAll('tr').length > 1) {
            updateStatus('cached', 'Using cached data');
        } else {
            renderError();
        }
    } finally {
        isLoading = false;
        elements.refreshBtn.classList.remove('loading');
    }
}

/**
 * Render data into BUY/SELL/NO SIGNAL sections
 */
function renderSignalSections(data) {
    if (!data || data.length === 0) {
        renderError();
        return;
    }
    
    // Separate data by signal type
    const buySignals = data.filter(item => item.signal === 'BUY');
    const sellSignals = data.filter(item => item.signal === 'SELL');
    const noSignals = data.filter(item => item.signal === 'WAIT' || !item.signal);
    
    // Render each section
    renderSection(elements.buyTableBody, buySignals, 'buy');
    renderSection(elements.sellTableBody, sellSignals, 'sell');
    renderSection(elements.noSignalTableBody, noSignals, 'no-signal');
    
    // Update counts
    elements.buyCount.textContent = `${buySignals.length} pairs`;
    elements.sellCount.textContent = `${sellSignals.length} pairs`;
    elements.noSignalCount.textContent = `${noSignals.length} pairs`;
}

/**
 * Render a specific signal section
 */
function renderSection(tbody, data, sectionType) {
    if (!data || data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="empty-state">No signals found</td>
            </tr>
        `;
        return;
    }
    
    const rows = data.map(item => {
        // Map timeframe data based on selected style
        const tf1Data = item[selectedTimeframes.tf1] || item.monthly;
        const tf2Data = item[selectedTimeframes.tf2] || item.weekly;
        const tf3Data = item[selectedTimeframes.tf3] || item.daily;
        
        return `
            <tr>
                <td class="symbol">${escapeHtml(item.symbol)}</td>
                <td>${renderBadge(tf1Data)}</td>
                <td>${renderBadge(tf2Data)}</td>
                <td>${renderBadge(tf3Data)}</td>
            </tr>
        `;
    }).join('');
    
    tbody.innerHTML = rows;
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
 * Format bias text for display
 */
function formatBiasText(bias) {
    return bias || 'NEUTRAL';
}

/**
 * Render error state
 */
function renderError() {
    const errorHtml = `
        <tr>
            <td colspan="4" class="empty-state">
                <div style="padding: 20px;">
                    <div style="font-size: 2rem; margin-bottom: 10px;">⚠️</div>
                    <div>Failed to load data</div>
                    <div style="font-size: 0.8rem; margin-top: 8px; color: #718096;">
                        Make sure the backend server is running
                    </div>
                </div>
            </td>
        </tr>
    `;
    
    elements.buyTableBody.innerHTML = errorHtml;
    elements.sellTableBody.innerHTML = errorHtml;
    elements.noSignalTableBody.innerHTML = errorHtml;
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
        renderSignalSections(data.data);
        updateStatus('cached', 'Cached data');
        elements.pairsCount.textContent = `${data.count} pairs`;
        
        lastUpdateTime = new Date(parseInt(cacheTimestamp));
        updateLastUpdateTime();

    } catch (error) {
        console.error('Cache load failed:', error);
    }
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
 * Toggle collapsible sections
 */
function toggleSection(header) {
    const content = header.nextElementSibling;
    const icon = header.querySelector('.collapse-icon');
    
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        content.style.maxHeight = content.scrollHeight + 'px';
        icon.textContent = '▼';
    } else {
        content.classList.add('collapsed');
        content.style.maxHeight = '0';
        icon.textContent = '▶';
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