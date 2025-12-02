/**
 * Gestionale Fibra - Dashboard JavaScript
 * 
 * Handles dashboard interactivity, API calls, and chart rendering.
 */

// API Base URL
const API_BASE = '/api';

/**
 * Fetch data from the API with error handling.
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} - API response data
 */
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Format date for display.
 * @param {string} dateStr - ISO date string
 * @returns {string} - Formatted date
 */
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('it-IT', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
    });
}

/**
 * Get status badge HTML.
 * @param {string} status - Work status
 * @returns {string} - Badge HTML
 */
function getStatusBadge(status) {
    const statusMap = {
        pending: { label: 'In Attesa', class: 'badge-pending' },
        assigned: { label: 'Assegnato', class: 'badge-assigned' },
        accepted: { label: 'Accettato', class: 'badge-accepted' },
        in_progress: { label: 'In Corso', class: 'badge-in-progress' },
        completed: { label: 'Completato', class: 'badge-completed' },
        refused: { label: 'Rifiutato', class: 'badge-refused' },
        cancelled: { label: 'Annullato', class: 'badge-cancelled' },
    };
    
    const info = statusMap[status] || { label: status, class: 'bg-secondary' };
    return `<span class="badge badge-status ${info.class}">${info.label}</span>`;
}

/**
 * Load and display statistics cards.
 */
async function loadStats() {
    try {
        const stats = await fetchAPI('/stats');
        
        // Calculate totals from daily stats
        let totalWorks = 0;
        let completedWorks = 0;
        let pendingWorks = 0;
        let inProgressWorks = 0;
        
        stats.daily_stats.forEach(day => {
            totalWorks += day.total_works;
            completedWorks += day.completed;
            pendingWorks += day.pending;
            inProgressWorks += day.in_progress;
        });
        
        // Update stat cards
        document.getElementById('totalWorks').textContent = totalWorks;
        document.getElementById('completedWorks').textContent = completedWorks;
        document.getElementById('pendingWorks').textContent = pendingWorks;
        document.getElementById('inProgressWorks').textContent = inProgressWorks;
        
        // Render charts
        renderDailyChart(stats.daily_stats);
        renderOperatorChart(stats.operator_stats);
        
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

/**
 * Render daily works chart.
 * @param {Array} dailyStats - Daily statistics data
 */
function renderDailyChart(dailyStats) {
    const ctx = document.getElementById('dailyChart');
    if (!ctx) return;
    
    const labels = dailyStats.map(d => formatDate(d.date));
    const completed = dailyStats.map(d => d.completed);
    const pending = dailyStats.map(d => d.pending);
    const inProgress = dailyStats.map(d => d.in_progress);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Completati',
                    data: completed,
                    backgroundColor: '#198754',
                },
                {
                    label: 'In Attesa',
                    data: pending,
                    backgroundColor: '#ffc107',
                },
                {
                    label: 'In Corso',
                    data: inProgress,
                    backgroundColor: '#6f42c1',
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { stacked: true },
                y: { stacked: true, beginAtZero: true },
            },
            plugins: {
                legend: {
                    position: 'bottom',
                },
            },
        },
    });
}

/**
 * Render operator distribution chart.
 * @param {Array} operatorStats - Operator statistics data
 */
function renderOperatorChart(operatorStats) {
    const ctx = document.getElementById('operatorChart');
    if (!ctx) return;
    
    const labels = operatorStats.map(o => o.operator);
    const data = operatorStats.map(o => o.total_works);
    const colors = [
        '#0d6efd', '#198754', '#dc3545', '#ffc107',
        '#0dcaf0', '#6f42c1', '#fd7e14', '#20c997',
    ];
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors.slice(0, labels.length),
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                },
            },
        },
    });
}

/**
 * Load and display recent works table.
 */
async function loadRecentWorks() {
    const tableBody = document.getElementById('recentWorksBody');
    if (!tableBody) return;
    
    try {
        const response = await fetchAPI('/works?size=10');
        
        if (response.items.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted py-4">
                        Nessun lavoro trovato
                    </td>
                </tr>
            `;
            return;
        }
        
        tableBody.innerHTML = response.items.map(work => `
            <tr>
                <td><strong>${work.wr_number}</strong></td>
                <td>${work.operator}</td>
                <td>${work.customer_name}</td>
                <td>${formatDate(work.scheduled_date)}</td>
                <td>${getStatusBadge(work.status)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary btn-action" 
                            onclick="viewWork(${work.id})">
                        <i class="bi bi-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger py-4">
                    Errore nel caricamento dei dati
                </td>
            </tr>
        `;
    }
}

/**
 * Load technicians for the technicians page.
 */
async function loadTechnicians() {
    const tableBody = document.getElementById('techniciansBody');
    if (!tableBody) return;
    
    try {
        const response = await fetchAPI('/technicians');
        
        if (response.items.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted py-4">
                        Nessun tecnico trovato
                    </td>
                </tr>
            `;
            return;
        }
        
        tableBody.innerHTML = response.items.map(tech => `
            <tr>
                <td>${tech.id}</td>
                <td><strong>${tech.name}</strong></td>
                <td>${tech.phone || '-'}</td>
                <td>${tech.email || '-'}</td>
                <td>
                    <span class="badge ${tech.is_active ? 'bg-success' : 'bg-secondary'}">
                        ${tech.is_active ? 'Attivo' : 'Inattivo'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary btn-action" 
                            onclick="editTechnician(${tech.id})">
                        <i class="bi bi-pencil"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger py-4">
                    Errore nel caricamento dei dati
                </td>
            </tr>
        `;
    }
}

/**
 * View work details.
 * @param {number} workId - Work order ID
 */
function viewWork(workId) {
    // In production, this would open a modal or navigate to details page
    console.log('View work:', workId);
    alert(`Visualizza lavoro ID: ${workId}`);
}

/**
 * Edit technician.
 * @param {number} techId - Technician ID
 */
function editTechnician(techId) {
    // In production, this would open an edit modal
    console.log('Edit technician:', techId);
    alert(`Modifica tecnico ID: ${techId}`);
}

/**
 * Initialize dashboard on page load.
 */
document.addEventListener('DOMContentLoaded', () => {
    // Load stats and charts
    loadStats();
    
    // Load recent works table
    loadRecentWorks();
    
    // Load technicians if on that page
    loadTechnicians();
});
