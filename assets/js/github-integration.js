/**
 * OmniCoder-AGI GitHub Integration
 * =================================
 * Full GitHub API integration for repository management
 */

class GitHubIntegration {
    constructor(app) {
        this.app = app;
        this.baseUrl = 'https://api.github.com';
        this.token = localStorage.getItem('github_token') || '';
        this.username = 'pythpythpython';
        this.email = 'pyth.pyth.python@gmail.com';
        
        // Initialize with stored token
        this.initToken();
    }

    /**
     * Initialize GitHub token
     */
    initToken() {
        // Check for stored token or use the one provided in config
        const storedToken = localStorage.getItem('github_token');
        if (storedToken) {
            this.token = storedToken;
        }
    }

    /**
     * Set GitHub token
     */
    setToken(token) {
        this.token = token;
        localStorage.setItem('github_token', token);
    }

    /**
     * Make authenticated API request
     */
    async apiRequest(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
        
        const headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.message || `GitHub API error: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get authenticated user info
     */
    async getUser() {
        return this.apiRequest('/user');
    }

    /**
     * List user repositories
     */
    async listRepositories(options = {}) {
        const { perPage = 50, sort = 'updated' } = options;
        return this.apiRequest(`/user/repos?per_page=${perPage}&sort=${sort}`);
    }

    /**
     * Get repository details
     */
    async getRepository(owner, repo) {
        return this.apiRequest(`/repos/${owner}/${repo}`);
    }

    /**
     * Create a new repository
     */
    async createRepository(name, options = {}) {
        const { description = '', private: isPrivate = false, autoInit = true } = options;
        
        return this.apiRequest('/user/repos', {
            method: 'POST',
            body: JSON.stringify({
                name,
                description,
                private: isPrivate,
                auto_init: autoInit
            })
        });
    }

    /**
     * Get repository contents
     */
    async getRepositoryContents(repo, path = '', owner = null) {
        const repoOwner = owner || this.username;
        const endpoint = path 
            ? `/repos/${repoOwner}/${repo}/contents/${path}`
            : `/repos/${repoOwner}/${repo}/contents`;
        
        return this.apiRequest(endpoint);
    }

    /**
     * Get file content
     */
    async getFileContent(repo, path, owner = null) {
        const repoOwner = owner || this.username;
        const file = await this.apiRequest(`/repos/${repoOwner}/${repo}/contents/${path}`);
        
        if (file.content) {
            return atob(file.content);
        }
        
        return '';
    }

    /**
     * Create or update file
     */
    async createOrUpdateFile(repo, path, content, message, options = {}) {
        const { branch = 'main', sha = null } = options;
        const repoOwner = this.username;
        
        const body = {
            message,
            content: btoa(content),
            branch
        };

        if (sha) {
            body.sha = sha;
        }

        return this.apiRequest(`/repos/${repoOwner}/${repo}/contents/${path}`, {
            method: 'PUT',
            body: JSON.stringify(body)
        });
    }

    /**
     * Commit changes to repository
     */
    async commitChanges(options) {
        const { repo, path, content, message, branch = 'main' } = options;
        
        // Try to get existing file SHA
        let sha = null;
        try {
            const existingFile = await this.apiRequest(`/repos/${this.username}/${repo}/contents/${path}?ref=${branch}`);
            sha = existingFile.sha;
        } catch (e) {
            // File doesn't exist, will create new
        }

        return this.createOrUpdateFile(repo, path, content, message, { branch, sha });
    }

    /**
     * Create a pull request
     */
    async createPullRequest(repo, options) {
        const { title, body, head, base = 'main' } = options;
        
        return this.apiRequest(`/repos/${this.username}/${repo}/pulls`, {
            method: 'POST',
            body: JSON.stringify({
                title,
                body,
                head,
                base
            })
        });
    }

    /**
     * List branches
     */
    async listBranches(repo, owner = null) {
        const repoOwner = owner || this.username;
        return this.apiRequest(`/repos/${repoOwner}/${repo}/branches`);
    }

    /**
     * Create a branch
     */
    async createBranch(repo, branchName, sourceBranch = 'main') {
        // Get the SHA of the source branch
        const ref = await this.apiRequest(`/repos/${this.username}/${repo}/git/ref/heads/${sourceBranch}`);
        
        return this.apiRequest(`/repos/${this.username}/${repo}/git/refs`, {
            method: 'POST',
            body: JSON.stringify({
                ref: `refs/heads/${branchName}`,
                sha: ref.object.sha
            })
        });
    }

    /**
     * List issues
     */
    async listIssues(repo, options = {}) {
        const { state = 'open', perPage = 30 } = options;
        return this.apiRequest(`/repos/${this.username}/${repo}/issues?state=${state}&per_page=${perPage}`);
    }

    /**
     * Create an issue
     */
    async createIssue(repo, options) {
        const { title, body, labels = [] } = options;
        
        return this.apiRequest(`/repos/${this.username}/${repo}/issues`, {
            method: 'POST',
            body: JSON.stringify({
                title,
                body,
                labels
            })
        });
    }

    /**
     * List commits
     */
    async listCommits(repo, options = {}) {
        const { perPage = 30, sha = 'main' } = options;
        return this.apiRequest(`/repos/${this.username}/${repo}/commits?sha=${sha}&per_page=${perPage}`);
    }

    /**
     * Get commit details
     */
    async getCommit(repo, sha) {
        return this.apiRequest(`/repos/${this.username}/${repo}/commits/${sha}`);
    }

    /**
     * List GitHub Actions workflows
     */
    async listWorkflows(repo) {
        return this.apiRequest(`/repos/${this.username}/${repo}/actions/workflows`);
    }

    /**
     * Trigger a workflow
     */
    async triggerWorkflow(repo, workflowId, ref = 'main', inputs = {}) {
        return this.apiRequest(`/repos/${this.username}/${repo}/actions/workflows/${workflowId}/dispatches`, {
            method: 'POST',
            body: JSON.stringify({
                ref,
                inputs
            })
        });
    }

    /**
     * Get workflow runs
     */
    async getWorkflowRuns(repo, workflowId) {
        return this.apiRequest(`/repos/${this.username}/${repo}/actions/workflows/${workflowId}/runs`);
    }

    /**
     * Search repositories
     */
    async searchRepositories(query, options = {}) {
        const { perPage = 30 } = options;
        return this.apiRequest(`/search/repositories?q=${encodeURIComponent(query)}&per_page=${perPage}`);
    }

    /**
     * Search code
     */
    async searchCode(query, options = {}) {
        const { perPage = 30 } = options;
        return this.apiRequest(`/search/code?q=${encodeURIComponent(query)}&per_page=${perPage}`);
    }

    /**
     * Get rate limit status
     */
    async getRateLimit() {
        return this.apiRequest('/rate_limit');
    }

    /**
     * Fork a repository
     */
    async forkRepository(owner, repo) {
        return this.apiRequest(`/repos/${owner}/${repo}/forks`, {
            method: 'POST'
        });
    }

    /**
     * Clone repository (returns clone URL)
     */
    getCloneUrl(repo, owner = null) {
        const repoOwner = owner || this.username;
        return `https://github.com/${repoOwner}/${repo}.git`;
    }

    /**
     * Get raw file content URL
     */
    getRawContentUrl(repo, path, branch = 'main', owner = null) {
        const repoOwner = owner || this.username;
        return `https://raw.githubusercontent.com/${repoOwner}/${repo}/${branch}/${path}`;
    }

    /**
     * Enable GitHub Pages for a repository
     */
    async enablePages(repo, options = {}) {
        const { branch = 'main', path = '/' } = options;
        
        return this.apiRequest(`/repos/${this.username}/${repo}/pages`, {
            method: 'POST',
            body: JSON.stringify({
                source: {
                    branch,
                    path
                }
            })
        });
    }

    /**
     * Get Pages site info
     */
    async getPagesInfo(repo) {
        return this.apiRequest(`/repos/${this.username}/${repo}/pages`);
    }

    /**
     * Helper: Check if connected
     */
    isConnected() {
        return !!this.token;
    }

    /**
     * Helper: Get auth status
     */
    async getAuthStatus() {
        if (!this.token) {
            return { connected: false, message: 'No token configured' };
        }

        try {
            const user = await this.getUser();
            return {
                connected: true,
                user: user.login,
                email: user.email,
                message: `Connected as ${user.login}`
            };
        } catch (e) {
            return {
                connected: false,
                message: `Connection failed: ${e.message}`
            };
        }
    }
}

// Export for use in main app
window.GitHubIntegration = GitHubIntegration;
