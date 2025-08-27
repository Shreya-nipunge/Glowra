// Authentication utilities
class AuthManager {
    constructor() {
        this.user = null;
        this.init();
    }

    init() {
        // Check for stored user data
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            this.user = JSON.parse(storedUser);
        }
    }

    async checkAuthState() {
        return new Promise((resolve) => {
            if (window.firebaseAuth) {
                window.firebaseAuth.onAuthStateChanged((user) => {
                    this.user = user;
                    resolve(user);
                });
            } else {
                resolve(this.user);
            }
        });
    }

    async getAuthToken() {
        if (window.firebaseAuth && window.firebaseAuth.currentUser) {
            try {
                return await window.firebaseAuth.currentUser.getIdToken();
            } catch (error) {
                console.error('Error getting auth token:', error);
                return null;
            }
        }
        return null;
    }

    logout() {
        this.user = null;
        localStorage.removeItem('user');
        if (window.firebaseAuth) {
            window.firebaseAuth.signOut();
        }
        window.location.href = '/';
    }

    isAuthenticated() {
        return this.user !== null;
    }

    getUserId() {
        return this.user ? this.user.uid : null;
    }

    getUserEmail() {
        return this.user ? this.user.email : null;
    }

    getUserName() {
        return this.user ? (this.user.displayName || this.user.email) : null;
    }
}

// Create global auth manager instance
window.authManager = new AuthManager();
