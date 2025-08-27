// Mood tracking functionality
class MoodTracker {
    constructor() {
        this.currentMood = 5;
        this.init();
    }

    init() {
        this.setupMoodSlider();
        this.setupSaveButton();
    }

    setupMoodSlider() {
        const slider = document.getElementById('moodSlider');
        const emoji = document.getElementById('moodEmoji');
        const label = document.getElementById('moodLabel');

        if (slider) {
            slider.addEventListener('input', (e) => {
                this.currentMood = parseInt(e.target.value);
                this.updateMoodDisplay(this.currentMood, emoji, label);
            });

            // Initialize display
            this.updateMoodDisplay(this.currentMood, emoji, label);
        }
    }

    updateMoodDisplay(mood, emoji, label) {
        const moodData = {
            1: { emoji: '😢', label: 'Very Low', color: '#ef4444' },
            2: { emoji: '😔', label: 'Low', color: '#f97316' },
            3: { emoji: '😐', label: 'Below Average', color: '#eab308' },
            4: { emoji: '🙂', label: 'Okay', color: '#84cc16' },
            5: { emoji: '😊', label: 'Good', color: '#22c55e' },
            6: { emoji: '😄', label: 'Great', color: '#10b981' },
            7: { emoji: '😃', label: 'Very Good', color: '#06b6d4' },
            8: { emoji: '😁', label: 'Excellent', color: '#3b82f6' },
            9: { emoji: '🤩', label: 'Amazing', color: '#6366f1' },
            10: { emoji: '🥳', label: 'Fantastic', color: '#8b5cf6' }
        };

        const data = moodData[mood] || moodData[5];
        
        if (emoji) emoji.textContent = data.emoji;
        if (label) label.textContent = `Feeling ${data.label}`;
        
        // Update slider track color
        const slider = document.getElementById('moodSlider');
        if (slider) {
            slider.style.setProperty('--thumb-color', data.color);
        }
    }

    setupSaveButton() {
        const saveBtn = document.getElementById('saveMoodBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveMoodEntry());
        }
    }

    async saveMoodEntry() {
        const notes = document.getElementById('moodNotes')?.value || '';
        const saveBtn = document.getElementById('saveMoodBtn');
        
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
        }

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
                    mood_value: this.currentMood,
                    notes: notes
                })
            });

            if (response.ok) {
                // Clear the notes field
                const notesField = document.getElementById('moodNotes');
                if (notesField) notesField.value = '';
                
                // Show success message
                window.dashboard?.showNotification('Mood entry saved successfully!', 'success');
                
                // Reload recent moods
                await this.loadRecentMoods();
                
                // Update overview stats
                if (window.dashboard) {
                    await window.dashboard.loadQuickStats();
                }
            } else {
                throw new Error('Failed to save mood entry');
            }
        } catch (error) {
            console.error('Error saving mood:', error);
            window.dashboard?.showNotification('Failed to save mood entry. Please try again.', 'error');
        } finally {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="fas fa-save me-2"></i>Save Mood Entry';
            }
        }
    }

    async loadRecentMoods() {
        const container = document.getElementById('recentMoods');
        if (!container) return;

        try {
            const token = await window.authManager.getAuthToken();
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch('/api/mood', { headers });
            
            if (response.ok) {
                const data = await response.json();
                const moods = data.moods || [];
                
                if (moods.length === 0) {
                    container.innerHTML = '<p class="text-muted">No mood entries yet today.</p>';
                    return;
                }

                container.innerHTML = moods.map(mood => {
                    const moodData = this.getMoodData(mood.mood_value);
                    const date = new Date(mood.created_at);
                    const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    
                    return `
                        <div class="d-flex align-items-center mb-3 p-2 border rounded">
                            <span class="fs-4 me-2">${moodData.emoji}</span>
                            <div class="flex-grow-1">
                                <small class="text-muted">${timeStr}</small>
                                <div class="fw-semibold">${moodData.label}</div>
                                ${mood.notes ? `<small class="text-muted">${mood.notes}</small>` : ''}
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                container.innerHTML = '<p class="text-muted">Unable to load recent moods.</p>';
            }
        } catch (error) {
            console.error('Error loading recent moods:', error);
            container.innerHTML = '<p class="text-muted">Error loading moods.</p>';
        }
    }

    getMoodData(value) {
        const moodData = {
            1: { emoji: '😢', label: 'Very Low' },
            2: { emoji: '😔', label: 'Low' },
            3: { emoji: '😐', label: 'Below Average' },
            4: { emoji: '🙂', label: 'Okay' },
            5: { emoji: '😊', label: 'Good' },
            6: { emoji: '😄', label: 'Great' },
            7: { emoji: '😃', label: 'Very Good' },
            8: { emoji: '😁', label: 'Excellent' },
            9: { emoji: '🤩', label: 'Amazing' },
            10: { emoji: '🥳', label: 'Fantastic' }
        };
        return moodData[value] || moodData[5];
    }
}

// Initialize mood tracker when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.moodTracker = new MoodTracker();
});
