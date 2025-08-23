// Main application logic
let moodChart = null;
let currentConversationId = null;

// Initialize dashboard
function initializeDashboard() {
    if (window.location.pathname === '/dashboard') {
        setupNavigation();
        setupEventListeners();
        loadDashboardData();
    }
}

// Setup navigation between sections
function setupNavigation() {
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const sections = ['dashboard', 'journal', 'chat', 'meditations'];
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            link.classList.add('active');
            
            // Hide all sections
            sections.forEach(section => {
                const element = document.getElementById(`${section}-section`);
                if (element) {
                    element.classList.add('d-none');
                }
            });
            
            // Show target section
            const target = link.getAttribute('href').substring(1); // Remove #
            const targetSection = document.getElementById(`${target}-section`);
            if (targetSection) {
                targetSection.classList.remove('d-none');
                
                // Load section-specific data
                loadSectionData(target);
            }
        });
    });
}

// Setup event listeners
function setupEventListeners() {
    // Quick action buttons
    const quickMoodBtn = document.getElementById('quick-mood-btn');
    if (quickMoodBtn) {
        quickMoodBtn.addEventListener('click', () => {
            const moodModal = new bootstrap.Modal(document.getElementById('moodModal'));
            moodModal.show();
        });
    }
    
    const quickJournalBtn = document.getElementById('quick-journal-btn');
    if (quickJournalBtn) {
        quickJournalBtn.addEventListener('click', () => {
            switchToSection('journal');
        });
    }
    
    const quickChatBtn = document.getElementById('quick-chat-btn');
    if (quickChatBtn) {
        quickChatBtn.addEventListener('click', () => {
            switchToSection('chat');
        });
    }
    
    const quickMeditationBtn = document.getElementById('quick-meditation-btn');
    if (quickMeditationBtn) {
        quickMeditationBtn.addEventListener('click', () => {
            switchToSection('meditations');
        });
    }
    
    // Mood form
    setupMoodForm();
    
    // Journal form
    setupJournalForm();
    
    // Chat form
    setupChatForm();
    
    // Range sliders in mood modal
    setupRangeSliders();
}

// Switch to specific section
function switchToSection(sectionName) {
    const navLink = document.querySelector(`[href="#${sectionName}"]`);
    if (navLink) {
        navLink.click();
    }
}

// Setup mood form
function setupMoodForm() {
    const saveMoodBtn = document.getElementById('save-mood-btn');
    if (saveMoodBtn) {
        saveMoodBtn.addEventListener('click', saveMoodLog);
    }
}

// Setup journal form
function setupJournalForm() {
    const journalText = document.getElementById('journal-text');
    const wordCount = document.getElementById('word-count');
    const saveBtnJournal = document.getElementById('journal-save-btn');
    const clearBtn = document.getElementById('journal-clear-btn');
    
    if (journalText && wordCount) {
        journalText.addEventListener('input', () => {
            const words = journalText.value.trim().split(/\s+/).filter(word => word.length > 0);
            wordCount.textContent = words.length;
        });
    }
    
    if (saveBtnJournal) {
        saveBtnJournal.addEventListener('click', saveJournalEntry);
    }
    
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            journalText.value = '';
            wordCount.textContent = '0';
        });
    }
}

// Setup chat form
function setupChatForm() {
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            sendChatMessage();
        });
    }
}

// Setup range sliders
function setupRangeSliders() {
    const energySlider = document.getElementById('energy-level');
    const stressSlider = document.getElementById('stress-level');
    const energyValue = document.getElementById('energy-value');
    const stressValue = document.getElementById('stress-value');
    
    if (energySlider && energyValue) {
        energySlider.addEventListener('input', () => {
            energyValue.textContent = energySlider.value;
        });
    }
    
    if (stressSlider && stressValue) {
        stressSlider.addEventListener('input', () => {
            stressValue.textContent = stressSlider.value;
        });
    }
}

// Load dashboard data
async function loadDashboardData() {
    try {
        await Promise.all([
            loadUserStats(),
            loadDailyPlan(),
            loadMoodChart(),
            loadBadges()
        ]);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load dashboard data');
    }
}

// Load user statistics
async function loadUserStats() {
    try {
        const response = await makeAuthenticatedRequest('/api/gamification/stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.data;
            
            // Update stat displays
            updateElement('current-streak', stats.overview?.current_streak || 0);
            updateElement('total-mood-logs', stats.activity_stats?.total_mood_logs || 0);
            updateElement('total-journal-entries', stats.activity_stats?.total_journal_entries || 0);
            updateElement('total-points', stats.overview?.total_points || 0);
            updateElement('completed-tasks', stats.overview?.total_completed_tasks || 0);
        }
    } catch (error) {
        console.error('Error loading user stats:', error);
    }
}

// Load daily plan
async function loadDailyPlan() {
    try {
        const response = await makeAuthenticatedRequest('/api/planner/today');
        const data = await response.json();
        
        const loadingEl = document.getElementById('daily-plan-loading');
        const contentEl = document.getElementById('daily-plan-content');
        const tasksListEl = document.getElementById('daily-tasks-list');
        
        if (loadingEl) loadingEl.classList.add('d-none');
        if (contentEl) contentEl.classList.remove('d-none');
        
        if (data.success && tasksListEl) {
            const plan = data.data;
            
            if (plan.tasks && plan.tasks.length > 0) {
                tasksListEl.innerHTML = plan.tasks.map(task => `
                    <div class="task-item d-flex align-items-center justify-content-between p-3 mb-2 border rounded">
                        <div class="task-info flex-grow-1">
                            <h6 class="task-title mb-1">${task.title}</h6>
                            <small class="text-muted">
                                <i data-feather="clock" class="me-1"></i>
                                ${task.estimated_minutes} minutes
                            </small>
                            ${task.description ? `<p class="task-description small text-muted mb-0 mt-1">${task.description}</p>` : ''}
                        </div>
                        <div class="task-actions">
                            ${task.status === 'completed' ? 
                                '<span class="badge bg-success"><i data-feather="check"></i> Done</span>' :
                                task.status === 'skipped' ?
                                '<span class="badge bg-secondary">Skipped</span>' :
                                `<div class="btn-group-sm">
                                    <button class="btn btn-sm btn-success complete-task-btn" data-task-id="${task.id}">
                                        <i data-feather="check"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-secondary skip-task-btn" data-task-id="${task.id}">
                                        <i data-feather="x"></i>
                                    </button>
                                </div>`
                            }
                        </div>
                    </div>
                `).join('');
                
                // Setup task action buttons
                setupTaskButtons();
            } else {
                tasksListEl.innerHTML = '<p class="text-muted text-center py-3">No tasks for today. Great job staying on top of your wellness!</p>';
            }
            
            feather.replace();
        }
    } catch (error) {
        console.error('Error loading daily plan:', error);
        const contentEl = document.getElementById('daily-plan-content');
        if (contentEl) {
            contentEl.innerHTML = '<p class="text-danger text-center py-3">Failed to load daily plan</p>';
            contentEl.classList.remove('d-none');
        }
    }
}

// Setup task action buttons
function setupTaskButtons() {
    // Complete task buttons
    document.querySelectorAll('.complete-task-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const taskId = btn.dataset.taskId;
            await completeTask(taskId);
        });
    });
    
    // Skip task buttons
    document.querySelectorAll('.skip-task-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const taskId = btn.dataset.taskId;
            await skipTask(taskId);
        });
    });
}

// Complete a task
async function completeTask(taskId) {
    try {
        const response = await makeAuthenticatedRequest(`/api/planner/task/${taskId}/complete`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(`Task completed! +${data.data.points_earned} points`);
            loadDailyPlan(); // Reload plan
            loadUserStats(); // Reload stats
        } else {
            showError(data.message || 'Failed to complete task');
        }
    } catch (error) {
        console.error('Error completing task:', error);
        showError('Failed to complete task');
    }
}

// Skip a task
async function skipTask(taskId) {
    try {
        const response = await makeAuthenticatedRequest(`/api/planner/task/${taskId}/skip`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('Task skipped');
            loadDailyPlan(); // Reload plan
        } else {
            showError(data.message || 'Failed to skip task');
        }
    } catch (error) {
        console.error('Error skipping task:', error);
        showError('Failed to skip task');
    }
}

// Load mood chart
async function loadMoodChart() {
    try {
        const response = await makeAuthenticatedRequest('/api/progress/mood-logs?limit=7');
        const data = await response.json();
        
        if (data.success) {
            const logs = data.data.logs || [];
            createMoodChart(logs);
        }
    } catch (error) {
        console.error('Error loading mood chart:', error);
    }
}

// Create mood chart
function createMoodChart(moodLogs) {
    const ctx = document.getElementById('mood-chart');
    if (!ctx) return;
    
    // Prepare chart data
    const last7Days = [];
    const today = new Date();
    
    for (let i = 6; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        last7Days.push(date.toISOString().split('T')[0]);
    }
    
    const chartData = last7Days.map(date => {
        const log = moodLogs.find(log => log.timestamp.startsWith(date));
        return log ? {
            mood: getMoodScore(log.mood),
            energy: log.energy,
            stress: 10 - log.stress // Invert stress so higher is better
        } : { mood: null, energy: null, stress: null };
    });
    
    const labels = last7Days.map(date => {
        const d = new Date(date);
        return d.toLocaleDateString('en-US', { weekday: 'short' });
    });
    
    // Destroy existing chart
    if (moodChart) {
        moodChart.destroy();
    }
    
    moodChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Mood',
                    data: chartData.map(d => d.mood),
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Energy',
                    data: chartData.map(d => d.energy),
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Low Stress',
                    data: chartData.map(d => d.stress),
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });
}

// Convert mood to numeric score
function getMoodScore(mood) {
    const scores = {
        'happy': 8,
        'neutral': 5,
        'stressed': 3,
        'anxious': 2,
        'sad': 1
    };
    return scores[mood] || 5;
}

// Load badges
async function loadBadges() {
    try {
        const response = await makeAuthenticatedRequest('/api/gamification/badges');
        const data = await response.json();
        
        const loadingEl = document.getElementById('badges-loading');
        const contentEl = document.getElementById('badges-content');
        const badgesListEl = document.getElementById('badges-list');
        
        if (loadingEl) loadingEl.classList.add('d-none');
        if (contentEl) contentEl.classList.remove('d-none');
        
        if (data.success && badgesListEl) {
            const badges = data.data.earned_badges || [];
            
            if (badges.length > 0) {
                badgesListEl.innerHTML = badges.slice(0, 3).map(badge => `
                    <div class="badge-item d-flex align-items-center p-2 mb-2 bg-light rounded">
                        <span class="badge-icon fs-4 me-3">${badge.icon}</span>
                        <div>
                            <h6 class="badge-name mb-0">${badge.name}</h6>
                            <small class="text-muted">${badge.description}</small>
                        </div>
                    </div>
                `).join('');
            } else {
                badgesListEl.innerHTML = '<p class="text-muted text-center py-3">No badges earned yet. Keep up your wellness journey!</p>';
            }
        }
    } catch (error) {
        console.error('Error loading badges:', error);
    }
}

// Save mood log
async function saveMoodLog() {
    try {
        const form = document.getElementById('mood-form');
        const formData = new FormData(form);
        
        const mood = formData.get('mood');
        if (!mood) {
            showError('Please select a mood');
            return;
        }
        
        const energy = parseInt(document.getElementById('energy-level').value);
        const stress = parseInt(document.getElementById('stress-level').value);
        const note = document.getElementById('mood-note').value;
        
        const response = await makeAuthenticatedRequest('/api/progress/mood-logs', {
            method: 'POST',
            body: JSON.stringify({
                mood: mood,
                energy: energy,
                stress: stress,
                note: note
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(`Mood logged! +${data.data.points_earned} points`);
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('moodModal'));
            modal.hide();
            
            // Reset form
            form.reset();
            document.getElementById('energy-level').value = 5;
            document.getElementById('stress-level').value = 5;
            document.getElementById('energy-value').textContent = '5';
            document.getElementById('stress-value').textContent = '5';
            
            // Reload data
            loadUserStats();
            loadMoodChart();
        } else {
            showError(data.message || 'Failed to save mood log');
        }
    } catch (error) {
        console.error('Error saving mood log:', error);
        showError('Failed to save mood log');
    }
}

// Save journal entry
async function saveJournalEntry() {
    try {
        const journalText = document.getElementById('journal-text').value.trim();
        
        if (!journalText) {
            showError('Please write something in your journal');
            return;
        }
        
        if (journalText.length < 10) {
            showError('Journal entry must be at least 10 characters long');
            return;
        }
        
        const saveBtnJournal = document.getElementById('journal-save-btn');
        saveBtnJournal.disabled = true;
        saveBtnJournal.innerHTML = '<i class="spinner-border spinner-border-sm me-2"></i>Analyzing...';
        
        const response = await makeAuthenticatedRequest('/api/journal/', {
            method: 'POST',
            body: JSON.stringify({
                text: journalText
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(`Journal entry saved! +${data.data.points_earned} points`);
            
            // Clear form
            document.getElementById('journal-text').value = '';
            document.getElementById('word-count').textContent = '0';
            
            // Show AI insights
            showJournalInsights(data.data.insight);
            
            // Reload data
            loadUserStats();
            loadRecentJournalEntries();
        } else {
            showError(data.message || 'Failed to save journal entry');
        }
    } catch (error) {
        console.error('Error saving journal entry:', error);
        showError('Failed to save journal entry');
    } finally {
        const saveBtnJournal = document.getElementById('journal-save-btn');
        saveBtnJournal.disabled = false;
        saveBtnJournal.innerHTML = '<i data-feather="send" class="me-2"></i>Submit Entry';
        feather.replace();
    }
}

// Show journal insights
function showJournalInsights(insight) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i data-feather="brain" class="me-2"></i>
                        AI Insights
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="insight-content">
                        <div class="mood-insight mb-4">
                            <h6 class="text-primary">Detected Mood</h6>
                            <p class="mood-display">
                                <span class="mood-emoji">${getMoodEmoji(insight.mood)}</span>
                                <span class="mood-text ms-2">${insight.mood.charAt(0).toUpperCase() + insight.mood.slice(1)}</span>
                            </p>
                        </div>
                        
                        <div class="message-insight mb-4">
                            <h6 class="text-primary">Supportive Message</h6>
                            <p class="message-text">${insight.message}</p>
                        </div>
                        
                        ${insight.categories && insight.categories.length > 0 ? `
                        <div class="categories-insight mb-4">
                            <h6 class="text-primary">Key Areas</h6>
                            <div class="categories-list">
                                ${insight.categories.map(cat => `<span class="badge bg-secondary me-2">${cat.replace('_', ' ')}</span>`).join('')}
                            </div>
                        </div>
                        ` : ''}
                        
                        ${insight.recommendations && insight.recommendations.length > 0 ? `
                        <div class="recommendations-insight">
                            <h6 class="text-primary">Recommendations</h6>
                            <div class="recommendations-list">
                                ${insight.recommendations.map(rec => `
                                    <div class="recommendation-item d-flex align-items-center p-2 mb-2 bg-light rounded">
                                        <i data-feather="${getRecommendationIcon(rec.type)}" class="text-primary me-3"></i>
                                        <div>
                                            <h6 class="mb-0">${rec.title}</h6>
                                            <small class="text-muted">${rec.duration_min} minutes</small>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        ` : ''}
                        
                        ${insight.escalation_advice ? `
                        <div class="alert alert-info mt-4">
                            <h6><i data-feather="heart" class="me-2"></i>Remember</h6>
                            <p class="mb-0">${insight.escalation_advice}</p>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    modal.addEventListener('hidden.bs.modal', () => {
        modal.remove();
    });
    
    feather.replace();
}

// Get mood emoji
function getMoodEmoji(mood) {
    const emojis = {
        'happy': '😊',
        'neutral': '😐',
        'stressed': '😰',
        'anxious': '😔',
        'sad': '😢'
    };
    return emojis[mood] || '😐';
}

// Get recommendation icon
function getRecommendationIcon(type) {
    const icons = {
        'breathing': 'wind',
        'movement': 'activity',
        'journaling': 'edit-3',
        'mindfulness': 'circle',
        'social': 'users'
    };
    return icons[type] || 'star';
}

// Send chat message
async function sendChatMessage() {
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, 'user');
    
    // Clear input
    chatInput.value = '';
    
    // Show typing indicator
    addTypingIndicator();
    
    try {
        const response = await makeAuthenticatedRequest('/api/chat/', {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                conversation_id: currentConversationId
            })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator();
        
        if (data.success) {
            currentConversationId = data.data.conversation_id;
            
            // Add AI response
            addChatMessage(data.data.response, 'ai');
            
            // Show suggestions if any
            if (data.data.suggestions && data.data.suggestions.length > 0) {
                showChatSuggestions(data.data.suggestions);
            }
        } else {
            addChatMessage('Sorry, I encountered an error. Please try again.', 'ai');
        }
    } catch (error) {
        console.error('Error sending chat message:', error);
        removeTypingIndicator();
        addChatMessage('Sorry, I\'m having trouble responding right now. Please try again later.', 'ai');
    }
}

// Add chat message to UI
function addChatMessage(message, sender) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const messageEl = document.createElement('div');
    messageEl.className = `chat-message ${sender} mb-3`;
    
    if (sender === 'user') {
        messageEl.innerHTML = `
            <div class="d-flex justify-content-end">
                <div class="message-content bg-primary text-white p-3 rounded-3" style="max-width: 70%;">
                    ${message}
                </div>
            </div>
        `;
    } else {
        messageEl.innerHTML = `
            <div class="d-flex">
                <div class="message-avatar me-3">
                    <div class="avatar bg-info text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                        <i data-feather="sun"></i>
                    </div>
                </div>
                <div class="message-content bg-light p-3 rounded-3" style="max-width: 70%;">
                    ${message}
                </div>
            </div>
        `;
    }
    
    chatMessages.appendChild(messageEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    feather.replace();
}

// Add typing indicator
function addTypingIndicator() {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const typingEl = document.createElement('div');
    typingEl.className = 'typing-indicator mb-3';
    typingEl.innerHTML = `
        <div class="d-flex">
            <div class="message-avatar me-3">
                <div class="avatar bg-info text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                    <i data-feather="sun"></i>
                </div>
            </div>
            <div class="message-content bg-light p-3 rounded-3">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(typingEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    feather.replace();
}

// Remove typing indicator
function removeTypingIndicator() {
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Show chat suggestions
function showChatSuggestions(suggestions) {
    const suggestionsEl = document.getElementById('suggestions-list');
    if (!suggestionsEl) return;
    
    suggestionsEl.innerHTML = suggestions.slice(0, 3).map(suggestion => `
        <button class="btn btn-sm btn-outline-secondary me-2 mb-2 suggestion-btn">
            ${suggestion}
        </button>
    `).join('');
    
    // Setup suggestion click handlers
    suggestionsEl.querySelectorAll('.suggestion-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.getElementById('chat-input').value = btn.textContent.trim();
        });
    });
}

// Load section-specific data
async function loadSectionData(section) {
    switch (section) {
        case 'journal':
            await loadRecentJournalEntries();
            break;
        case 'chat':
            await loadChatSuggestions();
            break;
        case 'meditations':
            await loadMeditations();
            break;
    }
}

// Load recent journal entries
async function loadRecentJournalEntries() {
    try {
        const response = await makeAuthenticatedRequest('/api/journal/?limit=5');
        const data = await response.json();
        
        const entriesListEl = document.getElementById('recent-entries-list');
        if (!entriesListEl) return;
        
        if (data.success && data.data.entries.length > 0) {
            entriesListEl.innerHTML = data.data.entries.map(entry => `
                <div class="entry-item p-3 mb-2 border rounded">
                    <div class="entry-meta d-flex justify-content-between align-items-center mb-2">
                        <small class="text-muted">
                            ${new Date(entry.timestamp).toLocaleDateString()}
                        </small>
                        <span class="mood-badge badge bg-secondary">
                            ${getMoodEmoji(entry.mood)} ${entry.mood}
                        </span>
                    </div>
                    <p class="entry-preview mb-0">
                        ${entry.text.substring(0, 100)}${entry.text.length > 100 ? '...' : ''}
                    </p>
                </div>
            `).join('');
        } else {
            entriesListEl.innerHTML = '<p class="text-muted text-center py-3">No journal entries yet. Start writing!</p>';
        }
    } catch (error) {
        console.error('Error loading journal entries:', error);
    }
}

// Load chat suggestions
async function loadChatSuggestions() {
    try {
        const response = await makeAuthenticatedRequest('/api/chat/suggestions');
        const data = await response.json();
        
        if (data.success) {
            showChatSuggestions(data.data.suggestions);
        }
    } catch (error) {
        console.error('Error loading chat suggestions:', error);
    }
}

// Load meditations
async function loadMeditations() {
    try {
        const response = await makeAuthenticatedRequest('/api/meditations/');
        const data = await response.json();
        
        const contentEl = document.getElementById('meditations-content');
        if (!contentEl) return;
        
        if (data.success) {
            const categories = data.data.categories;
            
            contentEl.innerHTML = Object.keys(categories).map(category => {
                const meditations = categories[category];
                if (meditations.length === 0) return '';
                
                return `
                    <div class="meditation-category mb-4">
                        <h5 class="category-title text-primary mb-3">
                            ${category.replace('_', ' ').toUpperCase()}
                        </h5>
                        <div class="row g-3">
                            ${meditations.map(meditation => `
                                <div class="col-md-6 col-lg-4">
                                    <div class="meditation-card card border-0 shadow-sm h-100">
                                        <div class="card-body">
                                            <h6 class="card-title">${meditation.name}</h6>
                                            <p class="card-text small text-muted">${meditation.description}</p>
                                            <div class="meditation-meta d-flex justify-content-between align-items-center mb-3">
                                                <small class="text-muted">
                                                    <i data-feather="clock" class="me-1"></i>
                                                    ${meditation.duration || 'Unknown'}
                                                </small>
                                                ${meditation.completed ? 
                                                    '<span class="badge bg-success">Completed</span>' : 
                                                    '<span class="badge bg-light text-dark">New</span>'
                                                }
                                            </div>
                                            <audio controls class="w-100 mb-2" style="height: 40px;">
                                                <source src="${meditation.url}" type="audio/mpeg">
                                                Your browser does not support the audio element.
                                            </audio>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }).join('');
            
            feather.replace();
        } else {
            contentEl.innerHTML = '<p class="text-center py-4">No meditations available at the moment.</p>';
        }
    } catch (error) {
        console.error('Error loading meditations:', error);
        const contentEl = document.getElementById('meditations-content');
        if (contentEl) {
            contentEl.innerHTML = '<p class="text-center py-4 text-danger">Failed to load meditations</p>';
        }
    }
}

// Utility function to update element text content
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

// Expose functions globally
window.initializeDashboard = initializeDashboard;
