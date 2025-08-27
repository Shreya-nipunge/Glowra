// Meditation library functionality
class MeditationLibrary {
    constructor() {
        this.meditations = [];
        this.currentAudio = null;
        this.init();
    }

    init() {
        // Initialize meditation library when the section becomes visible
    }

    async loadMeditations() {
        const container = document.getElementById('meditationLibrary');
        if (!container) return;

        try {
            const token = await window.authManager.getAuthToken();
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch('/api/meditation', { headers });
            
            if (response.ok) {
                const data = await response.json();
                this.meditations = data.meditations || [];
                
                if (this.meditations.length === 0) {
                    // Show default meditation library
                    this.loadDefaultMeditations();
                } else {
                    this.renderMeditations();
                }
            } else {
                this.loadDefaultMeditations();
            }
        } catch (error) {
            console.error('Error loading meditations:', error);
            this.loadDefaultMeditations();
        }
    }

    loadDefaultMeditations() {
        // Default meditation library when API is not available
        this.meditations = [
            {
                id: 1,
                title: "5-Minute Breathing Exercise",
                description: "A quick breathing exercise to center yourself and reduce stress.",
                duration: "5 min",
                category: "Breathing",
                image: "https://pixabay.com/get/g50eb32ba758c7467be8e9f2b396baadc156aa7c6bb5e5e49c21b2dd0c8f2da62a0a95b626089df282f126a9bf9f32273fe4f88a81613fbe76a668acb24dfcfbe_1280.jpg",
                audio_url: null
            },
            {
                id: 2,
                title: "Body Scan Meditation",
                description: "Progressive relaxation through mindful awareness of your body.",
                duration: "15 min",
                category: "Body Scan",
                image: "https://pixabay.com/get/g41aa5d0c7c05ca986c5adfc45566fbe054f74bf5b9edcbbcda0ef0e59cf5b38f319a7e0cde7b0981b5120cf8281948f8fe3c43760de1e7700eb62c8b2fc98341_1280.jpg",
                audio_url: null
            },
            {
                id: 3,
                title: "Mindful Morning",
                description: "Start your day with intention and positive energy.",
                duration: "10 min",
                category: "Morning",
                image: "https://pixabay.com/get/g0dc911bb27cb0b3bbb9ef71f9b44d50171c07ec3245f605292415a12595a034c39e9bc00963d20baa220eea450fe5d945c569a9ef1ec2fc2ecfb141b4e28dea3_1280.jpg",
                audio_url: null
            },
            {
                id: 4,
                title: "Sleep Preparation",
                description: "Wind down and prepare your mind for restful sleep.",
                duration: "20 min",
                category: "Sleep",
                image: "https://pixabay.com/get/g32048858c70e59cd6056111acd67690107dba44304eca3e61c4fedfa30790d9e5eb95a8b3bcea5da51a7689add38a5e61c076948596346eb95c0c7d5f00f7bdb_1280.jpg",
                audio_url: null
            },
            {
                id: 5,
                title: "Stress Relief",
                description: "Release tension and anxiety with guided relaxation.",
                duration: "12 min",
                category: "Stress Relief",
                image: "https://pixabay.com/get/gb74145b6ed581eac5ee5843b85dcb066d8e5252fb36773439069a252ca8e98d59bf85dec0240985a9a97484b19dbc33697ffce7d19a80c5ac33a1023fcbcc99c_1280.jpg",
                audio_url: null
            },
            {
                id: 6,
                title: "Focus & Concentration",
                description: "Enhance your mental clarity and focus with mindfulness.",
                duration: "8 min",
                category: "Focus",
                image: "https://pixabay.com/get/g90d2d7872045ef8af72b6f2dd993e917c15b0f205345611e25c71434129cbcab4766fdb9195acd77d259bf324ab5ec2c921b4ebb339a3dfbe71365d9f306657a_1280.jpg",
                audio_url: null
            }
        ];
        
        this.renderMeditations();
    }

    renderMeditations() {
        const container = document.getElementById('meditationLibrary');
        if (!container) return;

        const categories = [...new Set(this.meditations.map(m => m.category))];
        
        let html = '';
        
        categories.forEach(category => {
            const categoryMeditations = this.meditations.filter(m => m.category === category);
            
            html += `
                <div class="col-12 mb-4">
                    <h5 class="fw-bold text-primary mb-3">
                        <i class="fas fa-lotus-position me-2"></i>${category}
                    </h5>
                    <div class="row g-3">
                        ${categoryMeditations.map(meditation => this.renderMeditationCard(meditation)).join('')}
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    renderMeditationCard(meditation) {
        return `
            <div class="col-lg-4 col-md-6">
                <div class="card meditation-card border-0 shadow-sm h-100">
                    <img src="${meditation.image}" class="card-img-top" alt="${meditation.title}">
                    <div class="card-body">
                        <h6 class="card-title fw-bold">${meditation.title}</h6>
                        <p class="card-text text-muted small">${meditation.description}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="badge bg-primary">${meditation.duration}</span>
                            <button class="btn btn-sm btn-outline-primary" 
                                    onclick="meditationLibrary.startMeditation(${meditation.id})">
                                <i class="fas fa-play me-1"></i>Start
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    startMeditation(meditationId) {
        const meditation = this.meditations.find(m => m.id === meditationId);
        if (!meditation) return;

        // Stop any currently playing audio
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio = null;
        }

        // Show meditation modal
        this.showMeditationModal(meditation);
    }

    showMeditationModal(meditation) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('meditationModal');
        if (!modal) {
            modal = this.createMeditationModal();
        }

        // Update modal content
        const modalTitle = modal.querySelector('.modal-title');
        const modalBody = modal.querySelector('.modal-body');
        
        modalTitle.textContent = meditation.title;
        modalBody.innerHTML = `
            <div class="text-center">
                <img src="${meditation.image}" alt="${meditation.title}" 
                     class="img-fluid rounded mb-3" style="max-height: 200px;">
                <p class="text-muted">${meditation.description}</p>
                <div class="mb-4">
                    <span class="badge bg-primary fs-6">${meditation.duration}</span>
                </div>
                
                <div class="meditation-controls">
                    ${meditation.audio_url ? `
                        <audio id="meditationAudio" controls class="w-100 mb-3">
                            <source src="${meditation.audio_url}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                    ` : `
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i>
                            This is a guided meditation. Find a comfortable position, close your eyes, 
                            and follow along with the instructions.
                        </div>
                    `}
                    
                    <div class="meditation-timer" id="meditationTimer" style="display: none;">
                        <div class="circular-progress mb-3">
                            <div class="timer-display">
                                <span id="timerMinutes">00</span>:<span id="timerSeconds">00</span>
                            </div>
                        </div>
                        <button class="btn btn-outline-secondary" onclick="meditationLibrary.pauseTimer()">
                            <i class="fas fa-pause" id="pauseIcon"></i>
                            <span id="pauseText">Pause</span>
                        </button>
                    </div>
                </div>
                
                <div class="d-flex gap-2 justify-content-center">
                    ${!meditation.audio_url ? `
                        <button class="btn btn-primary" onclick="meditationLibrary.startTimer(${this.getDurationMinutes(meditation.duration)})">
                            <i class="fas fa-play me-2"></i>Start Session
                        </button>
                    ` : ''}
                    <button class="btn btn-success" onclick="meditationLibrary.completeMeditation()">
                        <i class="fas fa-check me-2"></i>Mark Complete
                    </button>
                </div>
            </div>
        `;

        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    createMeditationModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'meditationModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header border-0">
                        <h5 class="modal-title fw-bold"></h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Content will be dynamically inserted -->
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        return modal;
    }

    getDurationMinutes(durationStr) {
        const minutes = parseInt(durationStr.match(/\d+/)[0]);
        return minutes;
    }

    startTimer(minutes) {
        const timerDiv = document.getElementById('meditationTimer');
        const timerMinutes = document.getElementById('timerMinutes');
        const timerSeconds = document.getElementById('timerSeconds');
        
        if (!timerDiv || !timerMinutes || !timerSeconds) return;

        timerDiv.style.display = 'block';
        
        let totalSeconds = minutes * 60;
        this.timerInterval = setInterval(() => {
            const mins = Math.floor(totalSeconds / 60);
            const secs = totalSeconds % 60;
            
            timerMinutes.textContent = mins.toString().padStart(2, '0');
            timerSeconds.textContent = secs.toString().padStart(2, '0');
            
            if (totalSeconds <= 0) {
                clearInterval(this.timerInterval);
                this.completeMeditation();
                return;
            }
            
            totalSeconds--;
        }, 1000);
    }

    pauseTimer() {
        const pauseIcon = document.getElementById('pauseIcon');
        const pauseText = document.getElementById('pauseText');
        
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
            pauseIcon.className = 'fas fa-play';
            pauseText.textContent = 'Resume';
        } else {
            // Resume logic would need current timer state
            pauseIcon.className = 'fas fa-pause';
            pauseText.textContent = 'Pause';
        }
    }

    async completeMeditation() {
        try {
            // Clear any running timer
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
                this.timerInterval = null;
            }

            // Stop any audio
            if (this.currentAudio) {
                this.currentAudio.pause();
                this.currentAudio = null;
            }

            // Show completion message
            window.dashboard?.showNotification('Meditation session completed! Great job on taking time for yourself.', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('meditationModal'));
            if (modal) {
                modal.hide();
            }

            // TODO: Track meditation completion in backend
            // This could award points or update streaks
            
        } catch (error) {
            console.error('Error completing meditation:', error);
        }
    }
}

// Initialize meditation library when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.meditationLibrary = new MeditationLibrary();
});
