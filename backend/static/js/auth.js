// Firebase Auth handling
import { 
    signInWithRedirect, 
    GoogleAuthProvider, 
    getRedirectResult,
    onAuthStateChanged,
    signOut
} from 'https://www.gstatic.com/firebasejs/11.0.2/firebase-auth.js';

let currentUser = null;
let userToken = null;

// Initialize authentication
function initializeAuth() {
    const provider = new GoogleAuthProvider();
    
    // Check for redirect result
    getRedirectResult(window.auth)
        .then((result) => {
            if (result) {
                handleAuthSuccess(result.user);
            }
        })
        .catch((error) => {
            console.error('Auth redirect error:', error);
            showError('Authentication failed. Please try again.');
        });
    
    // Listen for auth state changes
    onAuthStateChanged(window.auth, (user) => {
        if (user) {
            handleAuthSuccess(user);
        } else {
            handleAuthLogout();
        }
    });
    
    // Set up event listeners
    setupAuthEventListeners(provider);
}

// Set up event listeners for auth buttons
function setupAuthEventListeners(provider) {
    // Login buttons
    const loginButtons = ['login-btn', 'get-started-btn', 'cta-signup-btn'];
    loginButtons.forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', () => {
                signInWithRedirect(window.auth, provider);
            });
        }
    });
    
    // Logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
}

// Handle successful authentication
async function handleAuthSuccess(user) {
    currentUser = user;
    
    try {
        // Get Firebase ID token
        userToken = await user.getIdToken();
        
        // Update UI
        updateAuthUI(user);
        
        // Create/update user profile
        await createUserProfile(user);
        
        // Redirect to dashboard if on homepage
        if (window.location.pathname === '/') {
            window.location.href = '/dashboard';
        }
        
    } catch (error) {
        console.error('Auth success handling error:', error);
        showError('Failed to complete authentication');
    }
}

// Handle logout
async function handleLogout() {
    try {
        await signOut(window.auth);
        handleAuthLogout();
    } catch (error) {
        console.error('Logout error:', error);
        showError('Failed to logout');
    }
}

// Handle logout state
function handleAuthLogout() {
    currentUser = null;
    userToken = null;
    
    // Update UI
    updateLogoutUI();
    
    // Redirect to homepage if on dashboard
    if (window.location.pathname === '/dashboard') {
        window.location.href = '/';
    }
}

// Update UI for authenticated user
function updateAuthUI(user) {
    // Hide auth buttons
    const authButtons = document.getElementById('auth-buttons');
    if (authButtons) {
        authButtons.classList.add('d-none');
    }
    
    // Show user menu
    const userMenu = document.getElementById('user-menu');
    if (userMenu) {
        userMenu.classList.remove('d-none');
    }
    
    // Update user name displays
    const displayName = user.displayName || user.email?.split('@')[0] || 'User';
    
    const userNameElements = ['user-name', 'user-display-name', 'welcome-name'];
    userNameElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = displayName;
        }
    });
}

// Update UI for logged out state
function updateLogoutUI() {
    // Show auth buttons
    const authButtons = document.getElementById('auth-buttons');
    if (authButtons) {
        authButtons.classList.remove('d-none');
    }
    
    // Hide user menu
    const userMenu = document.getElementById('user-menu');
    if (userMenu) {
        userMenu.classList.add('d-none');
    }
}

// Create user profile on backend
async function createUserProfile(user) {
    try {
        const response = await fetch('/api/auth/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${userToken}`
            },
            body: JSON.stringify({
                uid: user.uid,
                email: user.email,
                name: user.displayName || ''
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to create user profile');
        }
        
        const data = await response.json();
        console.log('User profile created:', data);
        
    } catch (error) {
        console.error('Profile creation error:', error);
        // Don't show error to user as this is not critical
    }
}

// Make authenticated API request
async function makeAuthenticatedRequest(url, options = {}) {
    if (!userToken) {
        throw new Error('User not authenticated');
    }
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${userToken}`
        }
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    const response = await fetch(url, mergedOptions);
    
    if (response.status === 401) {
        // Token expired, try to refresh
        if (currentUser) {
            try {
                userToken = await currentUser.getIdToken(true);
                mergedOptions.headers['Authorization'] = `Bearer ${userToken}`;
                return await fetch(url, mergedOptions);
            } catch (error) {
                console.error('Token refresh failed:', error);
                handleLogout();
                throw new Error('Authentication failed');
            }
        }
    }
    
    return response;
}

// Show error message
function showError(message) {
    // Create toast or alert
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-danger border-0 position-fixed top-0 end-0 m-3';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i data-feather="alert-circle" class="me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove from DOM after hiding
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
    
    // Re-initialize feather icons
    feather.replace();
}

// Show success message
function showSuccess(message) {
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-success border-0 position-fixed top-0 end-0 m-3';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i data-feather="check-circle" class="me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
    
    feather.replace();
}

// Expose functions globally
window.initializeAuth = initializeAuth;
window.makeAuthenticatedRequest = makeAuthenticatedRequest;
window.showError = showError;
window.showSuccess = showSuccess;
window.getCurrentUser = () => currentUser;
window.getUserToken = () => userToken;
