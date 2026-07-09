/* ==========================================================================
   NeuroSense AI — Charts & Data Visualizations (Chart.js + Heatmap Engine)
   ========================================================================== */

let shapChartInstance = null;
let distChartInstance = null;
let trendChartInstance = null;

/**
 * Generates the 30-Day Longitudinal Mood & Burnout Heatmap on the Student Dashboard
 */
function generateCalendarHeatmap() {
    const grid = document.getElementById('calendarHeatmap');
    if (!grid) return;
    grid.innerHTML = '';

    const categories = ['Calm', 'Mild Stress', 'Moderate', 'Severe'];
    const classes = ['heat-calm', 'heat-mild', 'heat-mod', 'heat-sev'];
    
    // Generate realistic student stress trajectory across 30 days of the semester
    for (let day = 1; day <= 30; day++) {
        const cell = document.createElement('div');
        cell.className = 'calendar-cell';
        
        let statusIndex = 0;
        if (day >= 12 && day <= 16) {
            // Midterm exam week surge
            statusIndex = Math.floor(Math.random() * 2) + 2; // Moderate/Severe
        } else if (day >= 25 && day <= 28) {
            // Final assignment submission week
            statusIndex = Math.floor(Math.random() * 2) + 1; // Mild/Moderate
        } else {
            statusIndex = Math.floor(Math.random() * 2); // Calm/Mild
        }
        
        cell.classList.add(classes[statusIndex]);
        cell.innerText = `Day ${day}`;
        cell.title = `Day ${day}: ${categories[statusIndex]} recorded (Combined Score: ${(statusIndex * 25) + 15}%)`;
        
        cell.onclick = () => {
            alert(`📅 Day ${day} Assessment Details:\n• Status: ${categories[statusIndex]}\n• Primary Biomarker: ${statusIndex >= 2 ? 'Elevated MFCC Vocal Tension & Exam Deadline keywords' : 'Stable Pitch & Calm vocabulary'}`);
        };
        
        grid.appendChild(cell);
    }
}

/**
 * Renders or updates the SHAP/Tree Acoustic Feature Attribution Horizontal Bar Chart
 */
function renderSHAPChart(topDrivers) {
    const canvas = document.getElementById('shapChartCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    if (shapChartInstance) {
        shapChartInstance.destroy();
    }
    
    if (!topDrivers or topDrivers.length === 0) {
        return;
    }
    
    const labels = topDrivers.map(d => d.feature_name.split(' (')[0]);
    const data = topDrivers.map(d => d.impact_percentage);
    const colors = topDrivers.map(d => d.direction === 'stress' ? 'rgba(244, 63, 94, 0.8)' : 'rgba(52, 211, 153, 0.8)');
    const borderColors = topDrivers.map(d => d.direction === 'stress' ? '#f43f5e' : '#34d399');
    
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Inter', sans-serif";
    
    shapChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Shapley Impact Attribution (%)',
                data: data,
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const item = topDrivers[context.dataIndex];
                            return `${item.impact_percentage}% impact toward ${item.direction === 'stress' ? 'Stress/Agitation' : 'Calm/Stability'}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#64748b' },
                    title: { display: true, text: 'Relative Contribution (%)', color: '#64748b', font: { size: 10 } }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#cbd5e1', font: { size: 11, weight: '500' } }
                }
            }
        }
    });
}

/**
 * Initializes charts on the Clinical Counselor Dashboard Portal
 */
function renderCounselorCharts() {
    const distCanvas = document.getElementById('categoryDistributionChart');
    const trendCanvas = document.getElementById('longitudinalTrendChart');
    if (!distCanvas || !trendCanvas) return;
    
    if (distChartInstance) distChartInstance.destroy();
    if (trendChartInstance) trendChartInstance.destroy();
    
    // Category Distribution Doughnut Chart
    distChartInstance = new Chart(distCanvas.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Academic Stress (Exams/Deadlines)', 'Calm / Normal', 'Non-Academic Stress (Personal/Financial)', 'Mixed Stress (Dual-Origin)'],
            datasets: [{
                data: [42, 31, 15, 12],
                backgroundColor: [
                    'rgba(56, 189, 248, 0.85)',
                    'rgba(52, 211, 153, 0.85)',
                    'rgba(251, 146, 60, 0.85)',
                    'rgba(192, 132, 252, 0.85)'
                ],
                borderColor: '#0f172a',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#cbd5e1', font: { size: 11 } } }
            }
        }
    });
    
    // Longitudinal Stress Velocity Trend Chart
    trendChartInstance = new Chart(trendCanvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4 (Midterms)', 'Week 5', 'Week 6', 'Week 7 (Finals)'],
            datasets: [
                {
                    label: 'High-Risk Cohort Avg Stress (%)',
                    data: [35, 42, 48, 78, 55, 60, 85],
                    borderColor: '#f43f5e',
                    backgroundColor: 'rgba(244, 63, 94, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5
                },
                {
                    label: 'Campus General Cohort Avg (%)',
                    data: [22, 25, 28, 45, 30, 34, 52],
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.05)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top', labels: { color: '#cbd5e1', font: { size: 11 } } }
            },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' }, max: 100 }
            }
        }
    });
}
