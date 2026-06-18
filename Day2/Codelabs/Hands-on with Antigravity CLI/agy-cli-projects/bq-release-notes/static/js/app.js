// State Management
let releaseNotes = [];
let filteredNotes = [];
let selectedNoteId = null;
let currentFilters = {
    search: '',
    category: 'all',
    sort: 'newest' // newest or oldest
};
let activeTweetStyle = 'standard';

// DOM Elements
const elements = {
    refreshBtn: document.getElementById('refresh-btn'),
    lastUpdatedText: document.getElementById('last-updated-text'),
    statusDot: document.querySelector('.status-dot'),
    searchInput: document.getElementById('search-input'),
    clearSearchBtn: document.getElementById('clear-search'),
    categoryFiltersContainer: document.getElementById('category-filters-container'),
    sortNewestBtn: document.getElementById('sort-newest'),
    sortOldestBtn: document.getElementById('sort-oldest'),
    statsTotal: document.getElementById('stats-total'),
    statsFiltered: document.getElementById('stats-filtered'),
    feedItemsContainer: document.getElementById('feed-items-container'),
    exportCsvBtn: document.getElementById('export-csv-btn'),
    themeToggleBtn: document.getElementById('theme-toggle-btn'),
    themeToggleText: document.getElementById('theme-toggle-text'),
    iconSun: document.querySelector('.icon-sun'),
    iconMoon: document.querySelector('.icon-moon'),
    
    // States
    loadingState: document.getElementById('loading-state'),
    errorState: document.getElementById('error-state'),
    errorMessage: document.getElementById('error-message'),
    retryBtn: document.getElementById('retry-btn'),
    emptyState: document.getElementById('empty-state'),
    resetFiltersBtn: document.getElementById('reset-filters-btn'),
    
    // Modal
    tweetModal: document.getElementById('tweet-modal'),
    closeModalBtn: document.getElementById('close-modal-btn'),
    tweetTextbox: document.getElementById('tweet-textbox'),
    charCountText: document.getElementById('char-count'),
    charRingProgress: document.getElementById('char-ring-progress'),
    copyTweetBtn: document.getElementById('copy-tweet-btn'),
    copyBtnText: document.getElementById('copy-btn-text'),
    postTweetBtn: document.getElementById('post-tweet-btn'),
    styleBtns: document.querySelectorAll('.style-btn'),
    sourceCategoryBadge: document.getElementById('source-category-badge'),
    sourceDateText: document.getElementById('source-date'),
    sourceSnippetText: document.getElementById('source-snippet')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initEventListeners();
    fetchReleaseNotes(false);
});

// Event Listeners
function initEventListeners() {
    // Refresh, Retry, and Export
    elements.refreshBtn.addEventListener('click', () => fetchReleaseNotes(true));
    elements.retryBtn.addEventListener('click', () => fetchReleaseNotes(true));
    elements.exportCsvBtn.addEventListener('click', exportToCSV);
    elements.themeToggleBtn.addEventListener('click', toggleTheme);
    
    // Search
    elements.searchInput.addEventListener('input', (e) => {
        currentFilters.search = e.target.value;
        elements.clearSearchBtn.style.display = currentFilters.search ? 'block' : 'none';
        applyFilters();
    });
    
    elements.clearSearchBtn.addEventListener('click', () => {
        elements.searchInput.value = '';
        currentFilters.search = '';
        elements.clearSearchBtn.style.display = 'none';
        applyFilters();
    });
    
    // Category Pills
    elements.categoryFiltersContainer.addEventListener('click', (e) => {
        const pill = e.target.closest('.filter-pill');
        if (!pill) return;
        
        // Remove active class from all pills
        elements.categoryFiltersContainer.querySelectorAll('.filter-pill').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Add active to clicked pill
        pill.classList.add('active');
        currentFilters.category = pill.dataset.category;
        applyFilters();
    });
    
    // Sorting
    elements.sortNewestBtn.addEventListener('click', () => {
        elements.sortNewestBtn.classList.add('active');
        elements.sortOldestBtn.classList.remove('active');
        currentFilters.sort = 'newest';
        applyFilters();
    });
    
    elements.sortOldestBtn.addEventListener('click', () => {
        elements.sortOldestBtn.classList.add('active');
        elements.sortNewestBtn.classList.remove('active');
        currentFilters.sort = 'oldest';
        applyFilters();
    });
    
    // Reset Filters Empty State
    elements.resetFiltersBtn.addEventListener('click', () => {
        elements.searchInput.value = '';
        currentFilters.search = '';
        elements.clearSearchBtn.style.display = 'none';
        
        elements.categoryFiltersContainer.querySelectorAll('.filter-pill').forEach(btn => {
            if (btn.dataset.category === 'all') btn.classList.add('active');
            else btn.classList.remove('active');
        });
        currentFilters.category = 'all';
        applyFilters();
    });
    
    // Modal events
    elements.closeModalBtn.addEventListener('click', closeModal);
    elements.tweetModal.addEventListener('click', (e) => {
        if (e.target === elements.tweetModal) closeModal();
    });
    
    // Textarea character checking
    elements.tweetTextbox.addEventListener('input', updateCharCount);
    
    // Style Switchers
    elements.styleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            elements.styleBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            activeTweetStyle = e.target.dataset.style;
            loadTweetTemplate();
        });
    });
    
    // Copy to clipboard
    elements.copyTweetBtn.addEventListener('click', copyTweetToClipboard);
    
    // Post to Twitter/X
    elements.postTweetBtn.addEventListener('click', postToTwitter);
}

// Fetch notes from Flask backend
async function fetchReleaseNotes(forceRefresh = false) {
    showLoading(true);
    elements.statusDot.classList.add('loading');
    elements.lastUpdatedText.textContent = "Updating feed...";
    
    try {
        const response = await fetch(`/api/release-notes?refresh=${forceRefresh}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        
        if (result.status === 'success') {
            releaseNotes = result.data;
            elements.lastUpdatedText.textContent = `Last synced: ${result.last_updated}`;
            
            // Calculate and display statistics / categories count
            updateCategoryCounts();
            
            // Render
            applyFilters();
            showLoading(false);
        } else {
            throw new Error(result.message || 'Failed to fetch release notes.');
        }
    } catch (error) {
        console.error("Fetch failed:", error);
        elements.errorMessage.textContent = error.message || "Failed to fetch release notes from Google Feed.";
        elements.lastUpdatedText.textContent = "Sync failed";
        elements.statusDot.classList.remove('loading');
        showLoading(false);
        showError(true);
    } finally {
        elements.statusDot.classList.remove('loading');
    }
}

// UI State Switchers
function showLoading(isLoading) {
    if (isLoading) {
        elements.loadingState.classList.remove('hidden');
        elements.errorState.classList.add('hidden');
        elements.emptyState.classList.add('hidden');
        elements.feedItemsContainer.classList.add('hidden');
    } else {
        elements.loadingState.classList.add('hidden');
    }
}

function showError(isError) {
    if (isError) {
        elements.errorState.classList.remove('hidden');
        elements.loadingState.classList.add('hidden');
        elements.emptyState.classList.add('hidden');
        elements.feedItemsContainer.classList.add('hidden');
    } else {
        elements.errorState.classList.add('hidden');
    }
}

function showEmpty(isEmpty) {
    if (isEmpty) {
        elements.emptyState.classList.remove('hidden');
        elements.feedItemsContainer.classList.add('hidden');
    } else {
        elements.emptyState.classList.add('hidden');
        elements.feedItemsContainer.classList.remove('hidden');
    }
}

// Calculate relative date text (e.g. "2 days ago")
function getRelativeTimeString(dateString) {
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (isNaN(date.getTime())) return '';
        
        if (diffDays < 0) {
            // Future dates (if timezone differences/offsets or mock data)
            return 'recent';
        }
        
        if (diffDays === 0) {
            if (diffHours === 0) {
                if (diffMins <= 0) return 'just now';
                return `${diffMins}m ago`;
            }
            return `${diffHours}h ago`;
        } else if (diffDays === 1) {
            return 'yesterday';
        } else if (diffDays < 7) {
            return `${diffDays}d ago`;
        } else {
            return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
        }
    } catch (e) {
        return '';
    }
}

// Update the badge counter on filters
function updateCategoryCounts() {
    const counts = {
        all: releaseNotes.length,
        Feature: 0,
        Announcement: 0,
        Issue: 0,
        Deprecation: 0
    };
    
    releaseNotes.forEach(note => {
        if (counts[note.category] !== undefined) {
            counts[note.category]++;
        }
    });
    
    document.getElementById('badge-all').textContent = counts.all;
    document.getElementById('badge-feature').textContent = counts.Feature;
    document.getElementById('badge-announcement').textContent = counts.Announcement;
    document.getElementById('badge-issue').textContent = counts.Issue;
    document.getElementById('badge-deprecation').textContent = counts.Deprecation;
    
    elements.statsTotal.textContent = releaseNotes.length;
}

// Apply Search, Category Filters, and Sort
function applyFilters() {
    filteredNotes = releaseNotes.filter(note => {
        // Search filter
        const matchesSearch = !currentFilters.search || 
            note.content_text.toLowerCase().includes(currentFilters.search.toLowerCase()) ||
            note.category.toLowerCase().includes(currentFilters.search.toLowerCase()) ||
            note.date.toLowerCase().includes(currentFilters.search.toLowerCase());
            
        // Category filter
        const matchesCategory = currentFilters.category === 'all' || 
            note.category.toLowerCase() === currentFilters.category.toLowerCase();
            
        return matchesSearch && matchesCategory;
    });
    
    // Sort
    filteredNotes.sort((a, b) => {
        const timeA = new Date(a.updated_iso).getTime();
        const timeB = new Date(b.updated_iso).getTime();
        
        if (currentFilters.sort === 'newest') {
            return timeB - timeA;
        } else {
            return timeA - timeB;
        }
    });
    
    elements.statsFiltered.textContent = filteredNotes.length;
    
    if (filteredNotes.length === 0) {
        showEmpty(true);
    } else {
        showEmpty(false);
        renderFeedItems();
    }
}

// Render Feed Cards
function renderFeedItems() {
    elements.feedItemsContainer.innerHTML = '';
    
    filteredNotes.forEach((note, index) => {
        const relativeTime = getRelativeTimeString(note.updated_iso);
        const relativeTimeHtml = relativeTime ? `<span class="card-relative-time">${relativeTime}</span>` : '';
        const catClass = note.category.toLowerCase().replace(/\s+/g, '-');
        
        const card = document.createElement('div');
        card.className = `feed-card category-${catClass}`;
        if (note.id === selectedNoteId) {
            card.classList.add('selected');
        }
        card.dataset.id = note.id;
        
        // Build card HTML
        card.innerHTML = `
            <div class="card-header">
                <div class="card-meta">
                    <span class="card-date">${note.date}</span>
                    ${relativeTimeHtml}
                </div>
                <span class="category-tag">${note.category}</span>
            </div>
            
            <div class="card-content">
                ${note.content_html}
            </div>
            
            <div class="card-actions" style="gap: 8px;">
                <button class="btn btn-secondary btn-card-copy" title="Copy release note text to clipboard">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                    <span>Copy</span>
                </button>
                <button class="btn btn-secondary btn-card-tweet" title="Draft Tweet about this update">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"></path>
                    </svg>
                    <span>Draft Tweet</span>
                </button>
            </div>
        `;
        
        // Listeners for selection, copying & tweeting
        card.addEventListener('click', (e) => {
            // Don't select if they click a link inside the card
            if (e.target.tagName === 'A') return;
            
            selectCard(note.id);
            
            // If they clicked the copy button inside card
            if (e.target.closest('.btn-card-copy')) {
                copyTextToClipboardDirect(note.content_text, e.target.closest('.btn-card-copy'));
            }
            
            // If they clicked the tweet button inside card
            if (e.target.closest('.btn-card-tweet')) {
                openTweetComposer(note);
            }
        });
        
        elements.feedItemsContainer.appendChild(card);
    });
}

function selectCard(noteId) {
    selectedNoteId = noteId;
    elements.feedItemsContainer.querySelectorAll('.feed-card').forEach(card => {
        if (card.dataset.id === noteId) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    });
}

// Tweet Composer Logic
let currentActiveNote = null;

function openTweetComposer(note) {
    currentActiveNote = note;
    
    // Set source details in modal
    elements.sourceCategoryBadge.textContent = note.category;
    elements.sourceCategoryBadge.className = `category-tag-inline category-${note.category.toLowerCase()}`;
    elements.sourceDateText.textContent = note.date;
    elements.sourceSnippetText.textContent = note.content_text;
    
    // Set style buttons
    elements.styleBtns.forEach(btn => {
        if (btn.dataset.style === 'standard') btn.classList.add('active');
        else btn.classList.remove('active');
    });
    activeTweetStyle = 'standard';
    
    // Generate draft text
    loadTweetTemplate();
    
    // Show Modal
    elements.tweetModal.classList.remove('hidden');
    elements.tweetTextbox.focus();
}

function closeModal() {
    elements.tweetModal.classList.add('hidden');
    currentActiveNote = null;
    resetCopyButton();
}

function loadTweetTemplate() {
    if (!currentActiveNote) return;
    
    const draftText = generateTweetDraft(
        activeTweetStyle, 
        currentActiveNote.category, 
        currentActiveNote.date, 
        currentActiveNote.content_text, 
        currentActiveNote.link
    );
    
    elements.tweetTextbox.value = draftText;
    updateCharCount();
}

function generateTweetDraft(style, category, date, text, link) {
    // Standard cleanup: collapse spaces
    let cleanText = text.replace(/\s+/g, ' ').trim();
    
    // Make sure we format date string nicely if it is long
    const shortDate = date;
    
    if (style === 'short') {
        const prefix = `BigQuery [${category}]: `;
        const suffix = `\n\nRead more: ${link}`;
        
        // Max content length we can allow
        const maxLen = 280 - prefix.length - suffix.length;
        let content = cleanText;
        if (cleanText.length > maxLen) {
            content = cleanText.substring(0, maxLen - 3) + "...";
        }
        
        return `${prefix}${content}${suffix}`;
    }
    
    if (style === 'punchy') {
        const prefix = `🚀 New BigQuery ${category}!\n\n`;
        const suffix = `\n\nFull details: ${link} #GoogleCloud #BigQuery`;
        
        const maxLen = 280 - prefix.length - suffix.length;
        let content = cleanText;
        if (cleanText.length > maxLen) {
            content = cleanText.substring(0, maxLen - 3) + "...";
        }
        return `${prefix}${content}${suffix}`;
    }
    
    // Default / Standard
    const prefix = `📢 BigQuery Update (${shortDate})\nCategory: ${category}\n\n`;
    const suffix = `\n\nLink: ${link}`;
    
    const maxLen = 280 - prefix.length - suffix.length;
    let content = cleanText;
    if (cleanText.length > maxLen) {
        content = cleanText.substring(0, maxLen - 3) + "...";
    }
    return `${prefix}${content}${suffix}`;
}

function updateCharCount() {
    const text = elements.tweetTextbox.value;
    const len = text.length;
    const remaining = 280 - len;
    
    elements.charCountText.textContent = remaining;
    
    // Update progress ring
    // Total circumference is 2 * PI * r (r=12) => approx 75.39
    const circumference = 75.39;
    const percent = Math.min(100, (len / 280) * 100);
    const offset = circumference - (percent / 100) * circumference;
    
    elements.charRingProgress.style.strokeDashoffset = offset;
    
    // Color thresholds
    elements.charRingProgress.classList.remove('warn', 'error');
    elements.charCountText.style.color = '';
    
    if (remaining < 0) {
        elements.charRingProgress.classList.add('error');
        elements.charCountText.style.color = 'var(--color-deprecation)';
        elements.postTweetBtn.disabled = true;
    } else if (remaining <= 20) {
        elements.charRingProgress.classList.add('warn');
        elements.charCountText.style.color = 'var(--color-issue)';
        elements.postTweetBtn.disabled = false;
    } else {
        elements.postTweetBtn.disabled = false;
    }
}

async function copyTweetToClipboard() {
    const text = elements.tweetTextbox.value;
    try {
        await navigator.clipboard.writeText(text);
        
        // Success state UI
        elements.copyTweetBtn.classList.add('copied-state');
        elements.copyBtnText.textContent = 'Copied!';
        
        const copyIcon = elements.copyTweetBtn.querySelector('svg');
        const originalIconHtml = copyIcon.innerHTML;
        
        // Replace with checkmark icon content
        copyIcon.innerHTML = `<polyline points="20 6 9 17 4 12"></polyline>`;
        
        setTimeout(() => {
            resetCopyButton();
            copyIcon.innerHTML = originalIconHtml;
        }, 2500);
    } catch (err) {
        console.error('Failed to copy text: ', err);
        alert('Could not copy text automatically. Please select the text in the preview and copy it manually.');
    }
}

function resetCopyButton() {
    elements.copyTweetBtn.classList.remove('copied-state');
    elements.copyBtnText.textContent = 'Copy Text';
}

function postToTwitter() {
    const text = elements.tweetTextbox.value;
    const tweetUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`;
    window.open(tweetUrl, '_blank', 'noopener,noreferrer');
}

async function copyTextToClipboardDirect(text, buttonEl) {
    try {
        await navigator.clipboard.writeText(text);
        const textEl = buttonEl.querySelector('span');
        const originalText = textEl.textContent;
        
        buttonEl.classList.add('copied-state');
        textEl.textContent = 'Copied!';
        
        const copyIcon = buttonEl.querySelector('svg');
        const originalIconHtml = copyIcon.innerHTML;
        copyIcon.innerHTML = `<polyline points="20 6 9 17 4 12"></polyline>`;
        
        setTimeout(() => {
            buttonEl.classList.remove('copied-state');
            textEl.textContent = originalText;
            copyIcon.innerHTML = originalIconHtml;
        }, 2000);
    } catch (err) {
        console.error('Failed to copy: ', err);
    }
}

function exportToCSV() {
    if (filteredNotes.length === 0) {
        alert("No release notes to export.");
        return;
    }
    
    // CSV Headers
    const headers = ["ID", "Date", "ISO Updated", "Category", "Documentation Link", "Content Text"];
    
    // CSV Rows
    const rows = filteredNotes.map(note => [
        note.id,
        note.date,
        note.updated_iso,
        note.category,
        note.link,
        note.content_text
    ]);
    
    // Escaping double quotes & special chars
    const escapeCSV = (val) => {
        if (val === null || val === undefined) return '';
        let formatted = String(val).replace(/"/g, '""');
        if (formatted.includes(',') || formatted.includes('\n') || formatted.includes('"')) {
            formatted = `"${formatted}"`;
        }
        return formatted;
    };
    
    const csvContent = [
        headers.map(escapeCSV).join(','),
        ...rows.map(row => row.map(escapeCSV).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    
    const timestamp = new Date().toISOString().slice(0, 10);
    const catSuffix = currentFilters.category !== 'all' ? `_${currentFilters.category.toLowerCase()}` : '';
    link.setAttribute("download", `bigquery_release_notes_${timestamp}${catSuffix}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Theme Handlers
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
}

function setTheme(theme) {
    if (theme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
        elements.iconSun.classList.add('hidden');
        elements.iconMoon.classList.remove('hidden');
        elements.themeToggleText.textContent = 'Dark Mode';
        localStorage.setItem('theme', 'light');
    } else {
        document.documentElement.removeAttribute('data-theme');
        elements.iconSun.classList.remove('hidden');
        elements.iconMoon.classList.add('hidden');
        elements.themeToggleText.textContent = 'Light Mode';
        localStorage.setItem('theme', 'dark');
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
}
