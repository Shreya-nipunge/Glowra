// Dashboard main functionality
class Dashboard {
    constructor() {
        this.currentSection = 'overview';
        this.init();
    }

    init() {
        this.setupNavigation();
        this.loadOverviewData();
        this.setupQuickActions();
        
        // Check authentication
        if (window.authManager) {
            window.authManager.checkAuthState().then(user => {
                if (!user) {
                    window.location.href = '/login';
                }
            });
        }
    }

    setupNavigation() {
        // Navigation menu clicks
        document.querySelectorAll('.nav-link[data-section]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.target.dataset.section;
                this.showSection(section);
            });
        });
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section-content').forEach(section => {
            section.classList.add('d-none');
        });

        // Show selected section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.remove('d-none');
        }

        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        const activeLink = document.querySelector(`.nav-link[data-section="${sectionName}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }

        this.currentSection = sectionName;

        // Load section-specific data
        this.loadSectionData(sectionName);
    }

    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'overview':
                await this.loadOverviewData();
                break;
            case 'mood':
                if (window.moodTracker) {
                    await window.moodTracker.loadRecentMoods();
                }
                break;
            case 'journal':
                if (window.journalManager) {
                    await window.journalManager.loadRecentEntries();
                }
                break;
            case 'plan':
                await this.loadDailyTasks();
                break;
            case 'meditation':
                if (window.meditationLibrary) {
                    await window.meditationLibrary.loadMeditations();
                }
                break;
            case 'analytics':
                if (window.analyticsManager) {
                    await window.analyticsManager.loadAnalytics();
                }
                break;
        }
    }

    async loadOverviewData() {
        try {
            // Load quick stats
            await this.loadQuickStats();
            await this.loadQuickTasks();
        } catch (error) {
            console.error('Error loading overview data:', error);
        }
    }

    async loadQuickStats() {
        try {
            const token = await window.authManager.getAuthToken();
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            // Load mood data
            const moodResponse = await fetch('/api/mood', { headers });
            if (moodResponse.ok) {
                const moodData = await moodResponse.json();
                // Update today's mood display
                if (moodData.today_mood) {
                    document.getElementById('todayMood').textContent = this.getMoodLabel(moodData.today_mood);
                }
            }

            // Load task data
            const tasksResponse = await fetch('/api/tasks', { headers });
            if (tasksResponse.ok) {
                const tasksData = await tasksResponse.json();
                document.getElementById('currentStreak').textContent = `${tasksData.streak || 0} days`;
                document.getElementById('totalPoints').textContent = tasksData.points || 0;
                
                const completed = tasksData.tasks ? tasksData.tasks.filter(t => t.completed).length : 0;
                const total = tasksData.tasks ? tasksData.tasks.length : 0;
                document.getElementById('tasksCompleted').textContent = `${completed}/${total}`;
            }

        } catch (error) {
            console.error('Error loading quick stats:', error);
        }
    }

    async loadQuickTasks() {
        const tasksList = document.getElementById('quickTasksList');
        
        try {
            const token = await window.authManager.getAuthToken();
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch('/api/tasks', { headers });
            
            if (response.ok) {
                const data = await response.json();
                const tasks = data.tasks || [];
                
                if (tasks.length === 0) {
                    tasksList.innerHTML = '<p class="text-muted">No tasks for today. Great job staying on top of things!</p>';
                    return;
                }

                const quickTasks = tasks.slice(0, 3); // Show only first 3 tasks
                tasksList.innerHTML = quickTasks.map(task => `
                    <div class="d-flex align-items-center mb-2">
                        <input type="checkbox" class="form-check-input me-2" 
                               ${task.completed ? 'checked' : ''} 
                               onchange="dashboard.toggleTask(${task.id}, this.checked)">
                        <span class="${task.completed ? 'text-decoration-line-through text-muted' : ''}">${task.title}</span>
                    </div>
                `).join('');
            } else {
                tasksList.innerHTML = '<p class="text-muted">Unable to load tasks at the moment.</p>';
            }
        } catch (error) {
            console.error('Error loading quick tasks:', error);
            tasksList.innerHTML = '<p class="text-muted">Error loading tasks.</p>';
        }
    }

    async loadDailyTasks() {
        const tasksList = document.getElementById('dailyTasksList');
        const taskProgress = document.getElementById('taskProgress');
        const streakCounter = document.getElementById('streakCounter');
        const pointsCounter = document.getElementById('pointsCounter');
        
        try {
            const token = await window.authManager.getAuthToken();
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch('/api/tasks', { headers });
            
            if (response.ok) {
                const data = await response.json();
                const tasks = data.tasks || [];
                
                // Update counters
                const completed = tasks.filter(t => t.completed).length;
                taskProgress.textContent = `${completed}/${tasks.length} Complete`;
                streakCounter.textContent = data.streak || 0;
                pointsCounter.textContent = data.points || 0;
                
                if (tasks.length === 0) {
                    tasksList.innerHTML = `
                        <div class="text-center py-4">
                            <i class="fas fa-check-circle fa-3x text-success mb-3"></i>
                            <h5>All caught up!</h5>
                            <p class="text-muted">No tasks for today. You're doing great!</p>
                        </div>
                    `;
                    return;
                }

                tasksList.innerHTML = tasks.map(task => `
                    <div class="task-item ${task.completed ? 'completed' : ''}">
                        <div class="d-flex align-items-center">
                            <input type="checkbox" class="form-check-input task-checkbox" 
                                   ${task.completed ? 'checked' : ''} 
                                   onchange="dashboard.toggleTask(${task.id}, this.checked)">
                            <div class="flex-grow-1">
                                <h6 class="mb-1 ${task.completed ? 'text-decoration-line-through' : ''}">${task.title}</h6>
                                ${task.description ? `<p class="mb-1 text-muted small">${task.description}</p>` : ''}
                                <small class="text-primary">+${task.points || 10} points</small>
                            </div>
                        </div>
                    </div>
                `).join('');
            } else {
                tasksList.innerHTML = '<p class="text-muted">Unable to load tasks at the moment.</p>';
            }
        } catch (error) {
            console.error('Error loading daily tasks:', error);
            tasksList.innerHTML = '<p class="text-muted">Error loading tasks.</p>';
        }
    }

    async toggleTask(taskId, completed) {
        try {
            const token = await window.authManager.getAuthToken();
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch('/api/tasks', {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify({
                    task_id: taskId,
                    completed: completed
                })
            });

            if (response.ok) {
                const data = await response.json();
                
                // Show points earned notification
                if (completed && data.points_earned) {
                    this.showNotification(`Great job! You earned ${data.points_earned} points!`, 'success');
                }
                
                // Reload the current section
                await this.loadSectionData(this.currentSection);
                
                // Update overview if we're not currently on it
                if (this.currentSection !== 'overview') {
                    await this.loadQuickStats();
                }
            }
        } catch (error) {
            console.error('Error toggling task:', error);
        }
    }

    setupQuickActions() {
        // Quick mood buttons
        document.querySelectorAll('.mood-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const mood = parseInt(e.target.dataset.mood);
                await this.saveQuickMood(mood);
            });
        });
    }

    async saveQuickMood(mood) {
        try {
            const token = await window.authManager.getAuthToken();
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch('/api/mood', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    mood_value: mood,
                    notes: 'Quick mood entry'
                })
            });

            if (response.ok) {
                this.showNotification('Mood recorded successfully!', 'success');
                await this.loadQuickStats();
            }
        } catch (error) {
            console.error('Error saving quick mood:', error);
        }
    }

    getMoodLabel(moodValue) {
        const labels = {
            1: '😢 Very Low',
            2: '😔 Low',
            3: '😐 Below Average',
            4: '🙂 Okay',
            5: '😊 Good',
            6: '😄 Great',
            7: '😃 Very Good',
            8: '😁 Excellent',
            9: '🤩 Amazing',
            10: '🥳 Fantastic'
        };
        return labels[moodValue] || '🙂 Okay';
    }

    showNotification(message, type = 'info') {
        // Create and show a Bootstrap toast notification
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'primary'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '11';
        document.body.appendChild(container);
        return container;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});

// Make showSection globally available
window.showSection = (sectionName) => {
    if (window.dashboard) {
        window.dashboard.showSection(sectionName);
    }
};
