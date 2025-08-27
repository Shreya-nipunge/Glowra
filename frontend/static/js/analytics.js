// Analytics dashboard functionality
class AnalyticsManager {
    constructor() {
        this.charts = {};
        this.init();
    }

    init() {
        // Initialize charts when analytics section becomes visible
    }

    async loadAnalytics() {
        try {
            await Promise.all([
                this.loadMoodTrends(),
                this.loadTaskCompletionStats(),
                this.loadWeeklySummary(),
                this.loadAchievementProgress()
            ]);
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }

    async loadMoodTrends() {
        const canvas = document.getElementById('moodTrendChart');
        if (!canvas) return;

        try {
            const token = await window.authManager.getAuthToken();
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch('/api/analytics', { headers });
            
            let moodData = [];
            if (response.ok) {
                const data = await response.json();
                moodData = data.mood_trends || [];
            }

            // If no data, create sample data for demonstration
            if (moodData.length === 0) {
                moodData = this.generateSampleMoodData();
            }

            this.createMoodTrendChart(canvas, moodData);
        } catch (error) {
            console.error('Error loading mood trends:', error);
            // Show sample data on error
            this.createMoodTrendChart(canvas, this.generateSampleMoodData());
        }
    }

    generateSampleMoodData() {
        const today = new Date();
        const data = [];
        
        for (let i = 29; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            
            // Generate realistic mood variation (3-8 range with some randomness)
            const baseMood = 5.5;
            const variation = (Math.random() - 0.5) * 3;
            const mood = Math.max(1, Math.min(10, baseMood + variation));
            
            data.push({
                date: date.toISOString().split('T')[0],
                mood: Math.round(mood * 10) / 10
            });
        }
        
        return data;
    }

    createMoodTrendChart(canvas, data) {
        // Destroy existing chart if it exists
        if (this.charts.moodTrend) {
            this.charts.moodTrend.destroy();
        }

        const ctx = canvas.getContext('2d');
        
        this.charts.moodTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => {
                    const date = new Date(d.date);
                    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                }),
                datasets: [{
                    label: 'Mood Level',
                    data: data.map(d => d.mood),
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#4f46e5',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#4f46e5',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return `Mood: ${context.parsed.y}/10`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        min: 1,
                        max: 10,
                        ticks: {
                            stepSize: 1,
                            callback: function(value) {
                                const moodLabels = {
                                    1: '😢', 2: '😔', 3: '😐', 4: '🙂', 5: '😊',
                                    6: '😄', 7: '😃', 8: '😁', 9: '🤩', 10: '🥳'
                                };
                                return moodLabels[value] || value;
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    async loadTaskCompletionStats() {
        const canvas = document.getElementById('taskCompletionChart');
        if (!canvas) return;

        try {
            const token = await window.authManager.getAuthToken();
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch('/api/tasks', { headers });
            
            let completionData = { completed: 0, pending: 0 };
            if (response.ok) {
                const data = await response.json();
                const tasks = data.tasks || [];
                completionData.completed = tasks.filter(t => t.completed).length;
                completionData.pending = tasks.filter(t => !t.completed).length;
            }

            // If no data, show sample
            if (completionData.completed === 0 && completionData.pending === 0) {
                completionData = { completed: 7, pending: 3 };
            }

            this.createTaskCompletionChart(canvas, completionData);
        } catch (error) {
            console.error('Error loading task completion stats:', error);
            this.createTaskCompletionChart(canvas, { completed: 7, pending: 3 });
        }
    }

    createTaskCompletionChart(canvas, data) {
        // Destroy existing chart if it exists
        if (this.charts.taskCompletion) {
            this.charts.taskCompletion.destroy();
        }

        const ctx = canvas.getContext('2d');
        
        this.charts.taskCompletion = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'Pending'],
                datasets: [{
                    data: [data.completed, data.pending],
                    backgroundColor: ['#10b981', '#f59e0b'],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    async loadWeeklySummary() {
        const container = document.getElementById('weeklySummary');
        if (!container) return;

        try {
            const token = await window.authManager.getAuthToken();
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch('/api/analytics', { headers });
            
            let summaryData = {};
            if (response.ok) {
                const data = await response.json();
                summaryData = data.weekly_summary || {};
            }

            // Generate sample data if none available
            if (Object.keys(summaryData).length === 0) {
                summaryData = this.generateSampleWeeklySummary();
            }

            this.renderWeeklySummary(container, summaryData);
        } catch (error) {
            console.error('Error loading weekly summary:', error);
            this.renderWeeklySummary(container, this.generateSampleWeeklySummary());
        }
    }

    generateSampleWeeklySummary() {
        return {
            average_mood: 6.8,
            tasks_completed: 15,
            journal_entries: 4,
            meditation_sessions: 3,
            streak_days: 5,
            mood_improvement: '+12%'
        };
    }

    renderWeeklySummary(container, data) {
        container.innerHTML = `
            <div class="row g-3">
                <div class="col-6">
                    <div class="d-flex align-items-center">
                        <div class="stat-icon bg-primary me-2" style="width: 30px; height: 30px;">
                            <i class="fas fa-smile text-white" style="font-size: 0.8rem;"></i>
                        </div>
                        <div>
                            <small class="text-muted">Avg Mood</small>
                            <div class="fw-bold">${data.average_mood}/10</div>
                        </div>
                    </div>
                </div>
                <div class="col-6">
                    <div class="d-flex align-items-center">
                        <div class="stat-icon bg-success me-2" style="width: 30px; height: 30px;">
                            <i class="fas fa-check text-white" style="font-size: 0.8rem;"></i>
                        </div>
                        <div>
                            <small class="text-muted">Tasks Done</small>
                            <div class="fw-bold">${data.tasks_completed}</div>
                        </div>
                    </div>
                </div>
                <div class="col-6">
                    <div class="d-flex align-items-center">
                        <div class="stat-icon bg-info me-2" style="width: 30px; height: 30px;">
                            <i class="fas fa-pen text-white" style="font-size: 0.8rem;"></i>
                        </div>
                        <div>
                            <small class="text-muted">Entries</small>
                            <div class="fw-bold">${data.journal_entries}</div>
                        </div>
                    </div>
                </div>
                <div class="col-6">
                    <div class="d-flex align-items-center">
                        <div class="stat-icon bg-warning me-2" style="width: 30px; height: 30px;">
                            <i class="fas fa-lotus-position text-white" style="font-size: 0.8rem;"></i>
                        </div>
                        <div>
                            <small class="text-muted">Meditations</small>
                            <div class="fw-bold">${data.meditation_sessions}</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-4 p-3 bg-light rounded">
                <div class="d-flex justify-content-between align-items-center">
                    <span class="fw-semibold">Mood Trend</span>
                    <span class="badge bg-success">${data.mood_improvement}</span>
                </div>
                <small class="text-muted">Your mood has been improving this week!</small>
            </div>
        `;
    }

    async loadAchievementProgress() {
        const container = document.getElementById('achievementProgress');
        if (!container) return;

        try {
            const token = await window.authManager.getAuthToken();
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch('/api/analytics', { headers });
            
            let achievements = [];
            if (response.ok) {
                const data = await response.json();
                achievements = data.achievements || [];
            }

            // Generate sample achievements if none available
            if (achievements.length === 0) {
                achievements = this.generateSampleAchievements();
            }

            this.renderAchievements(container, achievements);
        } catch (error) {
            console.error('Error loading achievements:', error);
            this.renderAchievements(container, this.generateSampleAchievements());
        }
    }

    generateSampleAchievements() {
        return [
            {
                title: "First Steps",
                description: "Complete your first mood entry",
                progress: 100,
                unlocked: true,
                icon: "fas fa-baby"
            },
            {
                title: "Consistent Tracker",
                description: "Log mood for 7 days straight",
                progress: 71,
                unlocked: false,
                icon: "fas fa-calendar-check"
            },
            {
                title: "Mindful Writer",
                description: "Write 10 journal entries",
                progress: 40,
                unlocked: false,
                icon: "fas fa-pen-fancy"
            },
            {
                title: "Zen Master",
                description: "Complete 20 meditation sessions",
                progress: 15,
                unlocked: false,
                icon: "fas fa-lotus-position"
            }
        ];
    }

    renderAchievements(container, achievements) {
        container.innerHTML = achievements.map(achievement => `
            <div class="achievement-item mb-3 p-3 border rounded ${achievement.unlocked ? 'bg-light-success' : ''}">
                <div class="d-flex align-items-center mb-2">
                    <i class="${achievement.icon} fa-lg me-3 ${achievement.unlocked ? 'text-success' : 'text-muted'}"></i>
                    <div class="flex-grow-1">
                        <h6 class="mb-0 ${achievement.unlocked ? 'text-success' : ''}">${achievement.title}</h6>
                        <small class="text-muted">${achievement.description}</small>
                    </div>
                    ${achievement.unlocked ? '<i class="fas fa-check-circle text-success"></i>' : ''}
                </div>
                ${!achievement.unlocked ? `
                    <div class="progress" style="height: 6px;">
                        <div class="progress-bar" style="width: ${achievement.progress}%"></div>
                    </div>
                    <small class="text-muted">${achievement.progress}% complete</small>
                ` : ''}
            </div>
        `).join('');
    }

    // Utility method to destroy all charts (useful for cleanup)
    destroyAllCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}

// Initialize analytics manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.analyticsManager = new AnalyticsManager();
});
