document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const bioText = document.getElementById('bioText');
    const bioCounter = document.getElementById('bioCounter');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const submitBtn = document.getElementById('submitBtn');
    const clearBtn = document.getElementById('clearBtn');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const apiUrl = document.getElementById('apiUrl');

    // Set API URL
    const currentUrl = window.location.origin;
    apiUrl.textContent = `${currentUrl}/api/bio_upload`;

    // Bio counter
    function updateCounter() {
        const length = bioText.value.length;
        bioCounter.textContent = `${length}/500`;
        bioCounter.className = length > 450 ? 'bio-counter status-warning' : 'bio-counter';
    }

    bioText.addEventListener('input', updateCounter);
    updateCounter();

    // Tab switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });

    // Clear results
    clearBtn.addEventListener('click', () => {
        results.innerHTML = `
            <div class="result-item">
                <div class="result-label">Cleared</div>
                <div class="result-value">Results cleared</div>
            </div>
        `;
    });

    // Format result
    function formatResult(key, value) {
        const div = document.createElement('div');
        div.className = 'result-item';
        
        const label = document.createElement('div');
        label.className = 'result-label';
        label.textContent = key.toUpperCase();
        
        const val = document.createElement('div');
        val.className = 'result-value';
        
        // Add status colors
        if (key === 'status') {
            if (value.includes('✅') || value.includes('Success')) {
                val.classList.add('status-success');
            } else if (value.includes('❌') || value.includes('Error')) {
                val.classList.add('status-error');
            } else if (value.includes('⚠️')) {
                val.classList.add('status-warning');
            }
        }
        
        val.textContent = value || 'N/A';
        
        div.appendChild(label);
        div.appendChild(val);
        
        return div;
    }

    // Submit form
    submitBtn.addEventListener('click', async () => {
        // Get active tab
        const activeTab = document.querySelector('.tab-btn.active');
        const method = activeTab.getAttribute('data-tab');
        
        // Get values
        const bio = bioText.value.trim();
        if (!bio) {
            alert('Please enter bio text');
            return;
        }
        
        let params = new URLSearchParams();
        params.append('bio', bio);
        
        if (method === 'jwt') {
            const jwt = document.getElementById('jwtToken').value.trim();
            if (!jwt) {
                alert('Please enter JWT token');
                return;
            }
            params.append('jwt', jwt);
        } else if (method === 'uid') {
            const uid = document.getElementById('uid').value.trim();
            const pass = document.getElementById('password').value.trim();
            if (!uid || !pass) {
                alert('Please enter both UID and Password');
                return;
            }
            params.append('uid', uid);
            params.append('pass', pass);
        } else if (method === 'access') {
            const access = document.getElementById('accessToken').value.trim();
            if (!access) {
                alert('Please enter Access Token');
                return;
            }
            params.append('access', access);
        }
        
        // Show loading
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> PROCESSING';
        loading.classList.add('active');
        
        try {
            const response = await fetch(`/api/bio_upload?${params.toString()}`);
            const data = await response.json();
            
            // Clear and show results
            results.innerHTML = '';
            for (const [key, value] of Object.entries(data)) {
                results.appendChild(formatResult(key, value));
            }
            
        } catch (error) {
            results.innerHTML = `
                <div class="result-item">
                    <div class="result-label">Error</div>
                    <div class="result-value status-error">${error.message}</div>
                </div>
            `;
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> UPDATE BIO';
            loading.classList.remove('active');
        }
    });

    // Example data (optional)
    document.getElementById('jwtToken').value = 'example.jwt.token';
    document.getElementById('uid').value = '123456789';
    document.getElementById('accessToken').value = 'example_access_token';
});
