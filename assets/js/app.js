/**
 * OmniCoder-AGI Main Application
 * ===============================
 * The World's Most Advanced Coding Automation AGI Suite
 */

class OmniCoderApp {
    constructor() {
        this.config = {
            github: {
                token: localStorage.getItem('github_token') || '',
                username: 'pythpythpython',
                email: 'pyth.pyth.python@gmail.com'
            },
            activeBoard: 'auto',
            multiAgentMode: false,
            learningMode: 'continuous',
            autoPushMerge: true
        };

        this.state = {
            currentRepo: 'OmniCoder-AGI',
            currentFile: null,
            messages: [],
            workHistory: [],
            isProcessing: false
        };

        this.agiEngines = null;
        this.mcpClient = null;
        this.githubClient = null;

        this.init();
    }

    async init() {
        console.log('🚀 Initializing OmniCoder-AGI...');
        
        // Initialize components
        this.initUI();
        this.initEventListeners();
        this.initMonacoEditor();
        
        // Load configuration
        await this.loadConfig();
        
        // Initialize AGI and MCP systems
        this.agiEngines = new AGIEngine(this);
        this.mcpClient = new MCPClient(this);
        this.githubClient = new GitHubIntegration(this);
        
        console.log('✅ OmniCoder-AGI initialized successfully');
    }

    initUI() {
        // Activity bar navigation
        document.querySelectorAll('.activity-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const panel = e.currentTarget.dataset.panel;
                this.switchActivityPanel(panel);
            });
        });

        // Settings button
        document.getElementById('settings-btn')?.addEventListener('click', () => {
            this.openSettings();
        });

        // Close settings
        document.getElementById('close-settings')?.addEventListener('click', () => {
            this.closeSettings();
        });

        // Settings navigation
        document.querySelectorAll('.settings-nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const section = e.currentTarget.dataset.section;
                this.switchSettingsSection(section);
            });
        });

        // Toggle switches
        document.querySelectorAll('.toggle-switch').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.currentTarget.classList.toggle('active');
            });
        });
    }

    initEventListeners() {
        // Repository search
        const repoSearch = document.getElementById('repo-search');
        repoSearch?.addEventListener('input', (e) => {
            this.filterRepositories(e.target.value);
        });

        // Repository selection
        document.querySelectorAll('.repo-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const repo = e.currentTarget.dataset.repo;
                this.selectRepository(repo);
            });
        });

        // AGI Board selection
        const boardSelect = document.getElementById('agi-board-select');
        boardSelect?.addEventListener('change', (e) => {
            this.config.activeBoard = e.target.value;
            this.showNotification(`Switched to ${e.target.options[e.target.selectedIndex].text} board`);
        });

        // Multi-agent toggle
        const multiAgentToggle = document.getElementById('multi-agent-toggle');
        multiAgentToggle?.addEventListener('click', () => {
            this.config.multiAgentMode = !this.config.multiAgentMode;
            multiAgentToggle.classList.toggle('active');
            this.showNotification(`Multi-Agent Mode ${this.config.multiAgentMode ? 'enabled' : 'disabled'}`);
        });

        // Send button
        const sendBtn = document.getElementById('send-btn');
        sendBtn?.addEventListener('click', () => this.sendMessage());

        // Enter key to send
        const agentInput = document.getElementById('agent-input');
        agentInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Quick action buttons
        document.getElementById('start-coding')?.addEventListener('click', () => {
            document.getElementById('agent-input')?.focus();
        });

        document.getElementById('open-repo')?.addEventListener('click', () => {
            this.openRepoSelector();
        });

        document.getElementById('view-boards')?.addEventListener('click', () => {
            this.showAGIBoards();
        });

        // File attachment
        document.getElementById('attach-file')?.addEventListener('click', () => {
            this.attachFile();
        });

        // Add context
        document.getElementById('add-context')?.addEventListener('click', () => {
            this.addContext();
        });

        // Upgrade submission
        document.getElementById('submit-upgrade')?.addEventListener('click', () => {
            this.submitUpgradeRequest();
        });

        // Add MCP server
        document.getElementById('add-mcp-btn')?.addEventListener('click', () => {
            this.addMCPServer();
        });

        // Close settings overlay on background click
        document.getElementById('settings-overlay')?.addEventListener('click', (e) => {
            if (e.target.id === 'settings-overlay') {
                this.closeSettings();
            }
        });
    }

    initMonacoEditor() {
        // Initialize Monaco Editor
        require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' }});
        
        require(['vs/editor/editor.main'], () => {
            // Define VS Code Dark theme
            monaco.editor.defineTheme('omnicoder-dark', {
                base: 'vs-dark',
                inherit: true,
                rules: [],
                colors: {
                    'editor.background': '#1e1e1e',
                }
            });

            this.editor = monaco.editor.create(document.getElementById('monaco-editor'), {
                value: '// Welcome to OmniCoder-AGI\n// Start coding or ask the AGI agent for help!\n\n',
                language: 'javascript',
                theme: 'omnicoder-dark',
                minimap: { enabled: true },
                fontSize: 14,
                fontFamily: "'Fira Code', 'Consolas', monospace",
                lineNumbers: 'on',
                automaticLayout: true,
                tabSize: 2,
                wordWrap: 'on'
            });

            // Hide editor initially (show welcome screen)
            document.getElementById('monaco-editor').style.display = 'none';
        });
    }

    async loadConfig() {
        // Load saved configuration
        const savedConfig = localStorage.getItem('omnicoder_config');
        if (savedConfig) {
            try {
                const config = JSON.parse(savedConfig);
                this.config = { ...this.config, ...config };
            } catch (e) {
                console.error('Error loading config:', e);
            }
        }
    }

    saveConfig() {
        localStorage.setItem('omnicoder_config', JSON.stringify(this.config));
    }

    switchActivityPanel(panel) {
        // Update activity bar
        document.querySelectorAll('.activity-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-panel="${panel}"]`)?.classList.add('active');

        // Update sidebar header
        const sidebarHeader = document.querySelector('.sidebar-header span');
        const panelNames = {
            explorer: 'Explorer',
            search: 'Search',
            git: 'Source Control',
            agents: 'AGI Agents',
            mcp: 'MCP Servers',
            testing: 'Testing & Training',
            account: 'Account'
        };
        if (sidebarHeader) {
            sidebarHeader.textContent = panelNames[panel] || 'Explorer';
        }
    }

    openSettings() {
        document.getElementById('settings-overlay')?.classList.add('active');
    }

    closeSettings() {
        document.getElementById('settings-overlay')?.classList.remove('active');
    }

    switchSettingsSection(section) {
        // Update navigation
        document.querySelectorAll('.settings-nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`)?.classList.add('active');

        // Show section
        document.querySelectorAll('.settings-section').forEach(s => {
            s.style.display = 'none';
        });
        document.getElementById(`section-${section}`)?.style.display = 'block';
    }

    filterRepositories(query) {
        const items = document.querySelectorAll('.repo-item');
        items.forEach(item => {
            const repoName = item.dataset.repo.toLowerCase();
            item.style.display = repoName.includes(query.toLowerCase()) ? 'flex' : 'none';
        });
    }

    async selectRepository(repo) {
        if (repo === 'new') {
            await this.createNewRepository();
            return;
        }

        // Update UI
        document.querySelectorAll('.repo-item').forEach(item => {
            item.classList.remove('selected');
        });
        document.querySelector(`[data-repo="${repo}"]`)?.classList.add('selected');

        this.state.currentRepo = repo;
        this.showNotification(`Selected repository: ${repo}`);

        // Load repository files
        await this.loadRepositoryFiles(repo);
    }

    async createNewRepository() {
        const name = prompt('Enter new repository name:');
        if (!name) return;

        this.showNotification('Creating new repository...');
        
        // This would call the GitHub API to create the repo
        if (this.githubClient) {
            try {
                await this.githubClient.createRepository(name);
                this.showNotification(`Repository ${name} created successfully!`);
            } catch (e) {
                this.showNotification(`Error creating repository: ${e.message}`, 'error');
            }
        }
    }

    async loadRepositoryFiles(repo) {
        // This would load files from GitHub
        if (this.githubClient) {
            try {
                const files = await this.githubClient.getRepositoryContents(repo);
                this.renderFileTree(files);
            } catch (e) {
                console.error('Error loading files:', e);
            }
        }
    }

    renderFileTree(files) {
        // Render file tree in sidebar
        const fileTree = document.getElementById('file-tree');
        if (!fileTree) return;

        // Clear existing items (except root)
        const items = fileTree.querySelectorAll('.file-item:not(:first-child)');
        items.forEach(item => item.remove());

        // Add files
        files.forEach(file => {
            const item = document.createElement('div');
            item.className = 'file-item';
            item.style.paddingLeft = '36px';
            item.dataset.path = file.path;
            
            const iconClass = this.getFileIconClass(file.name);
            item.innerHTML = `
                <i class="${iconClass}"></i>
                <span>${file.name}</span>
            `;
            
            item.addEventListener('click', () => this.openFile(file));
            fileTree.appendChild(item);
        });
    }

    getFileIconClass(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const icons = {
            js: 'fab fa-js file-js',
            ts: 'fab fa-js file-ts',
            py: 'fab fa-python file-py',
            rs: 'fab fa-rust file-rs',
            html: 'fab fa-html5 file-html',
            css: 'fab fa-css3 file-css',
            json: 'fas fa-file-code',
            md: 'fab fa-markdown',
            yml: 'fas fa-file-code',
            yaml: 'fas fa-file-code'
        };
        return icons[ext] || 'fas fa-file';
    }

    async openFile(file) {
        // Hide welcome screen, show editor
        document.getElementById('welcome-screen').style.display = 'none';
        document.getElementById('monaco-editor').style.display = 'block';

        // Add tab
        this.addEditorTab(file.name, file.path);

        // Load file content
        if (this.githubClient) {
            try {
                const content = await this.githubClient.getFileContent(this.state.currentRepo, file.path);
                this.editor.setValue(content);
                
                // Set language
                const ext = file.name.split('.').pop();
                const languageMap = {
                    js: 'javascript',
                    ts: 'typescript',
                    py: 'python',
                    rs: 'rust',
                    html: 'html',
                    css: 'css',
                    json: 'json',
                    md: 'markdown',
                    yml: 'yaml',
                    yaml: 'yaml'
                };
                monaco.editor.setModelLanguage(this.editor.getModel(), languageMap[ext] || 'plaintext');
            } catch (e) {
                console.error('Error loading file:', e);
            }
        }

        this.state.currentFile = file;
    }

    addEditorTab(name, path) {
        const tabs = document.querySelector('.editor-tabs');
        
        // Check if tab already exists
        if (document.querySelector(`[data-file="${path}"]`)) {
            this.activateTab(path);
            return;
        }

        // Create new tab
        const tab = document.createElement('div');
        tab.className = 'editor-tab';
        tab.dataset.file = path;
        tab.innerHTML = `
            <i class="${this.getFileIconClass(name)}"></i>
            <span>${name}</span>
            <span class="close-btn"><i class="fas fa-times"></i></span>
        `;

        tab.addEventListener('click', () => this.activateTab(path));
        tab.querySelector('.close-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.closeTab(path);
        });

        tabs.appendChild(tab);
        this.activateTab(path);
    }

    activateTab(path) {
        document.querySelectorAll('.editor-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-file="${path}"]`)?.classList.add('active');
    }

    closeTab(path) {
        const tab = document.querySelector(`[data-file="${path}"]`);
        if (tab) {
            tab.remove();
            
            // If no tabs left, show welcome screen
            if (document.querySelectorAll('.editor-tab').length === 0) {
                document.getElementById('welcome-screen').style.display = 'flex';
                document.getElementById('monaco-editor').style.display = 'none';
            }
        }
    }

    async sendMessage() {
        const input = document.getElementById('agent-input');
        const message = input.value.trim();
        
        if (!message || this.state.isProcessing) return;

        this.state.isProcessing = true;
        input.value = '';

        // Add user message
        this.addMessage('user', message);

        // Process with AGI
        try {
            const response = await this.agiEngines.processRequest(message, {
                board: this.config.activeBoard,
                multiAgent: this.config.multiAgentMode,
                context: {
                    currentRepo: this.state.currentRepo,
                    currentFile: this.state.currentFile,
                    editorContent: this.editor?.getValue() || ''
                }
            });

            // Add AGI response
            this.addMessage('agent', response.message);

            // Handle code changes
            if (response.codeChanges) {
                await this.applyCodeChanges(response.codeChanges);
            }

            // Handle work output
            if (response.workOutput) {
                this.showWorkOutput(response.workOutput);
            }

        } catch (e) {
            this.addMessage('agent', `Error processing request: ${e.message}`);
        }

        this.state.isProcessing = false;
    }

    addMessage(type, content) {
        const messagesContainer = document.getElementById('agent-messages');
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        const messageEl = document.createElement('div');
        messageEl.className = 'message';
        messageEl.innerHTML = `
            <div class="message-header">
                <div class="message-avatar ${type}">
                    <i class="fas fa-${type === 'user' ? 'user' : 'robot'}"></i>
                </div>
                <span class="message-sender">${type === 'user' ? 'You' : 'OmniCoder-AGI'}</span>
                <span class="message-time">${timeStr}</span>
            </div>
            <div class="message-content">${this.formatMessage(content)}</div>
        `;

        messagesContainer.appendChild(messageEl);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        this.state.messages.push({ type, content, time: now });
    }

    formatMessage(content) {
        // Convert markdown-like syntax to HTML
        return content
            .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }

    async applyCodeChanges(changes) {
        if (this.editor && changes.content) {
            this.editor.setValue(changes.content);
        }

        // Auto-commit if enabled
        if (this.config.autoPushMerge) {
            await this.commitAndPush(changes);
        }
    }

    async commitAndPush(changes) {
        if (this.githubClient) {
            try {
                const result = await this.githubClient.commitChanges({
                    repo: this.state.currentRepo,
                    path: this.state.currentFile?.path || 'new-file.js',
                    content: changes.content,
                    message: changes.commitMessage || 'Update from OmniCoder-AGI'
                });

                this.showWorkOutput({
                    type: 'commit',
                    message: 'Changes committed and pushed',
                    url: result.commit?.html_url
                });
            } catch (e) {
                console.error('Error committing:', e);
            }
        }
    }

    showWorkOutput(output) {
        const workOutputEl = document.getElementById('work-output');
        if (!workOutputEl) return;

        workOutputEl.style.display = 'block';
        workOutputEl.innerHTML = `
            <h4><i class="fas fa-check-circle" style="color: var(--success);"></i> Latest Work Completed</h4>
            <div class="work-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>${output.message}</span>
                    ${output.url ? `<a href="${output.url}" class="work-link" target="_blank">View ${output.type === 'commit' ? 'Commit' : 'Work'} →</a>` : ''}
                </div>
            </div>
        `;

        this.state.workHistory.push(output);
    }

    attachFile() {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.accept = '*/*';
        
        input.onchange = (e) => {
            const files = Array.from(e.target.files);
            files.forEach(file => {
                this.showNotification(`Attached: ${file.name}`);
            });
        };
        
        input.click();
    }

    addContext() {
        const context = prompt('Enter context (file path, URL, or description):');
        if (context) {
            this.showNotification(`Context added: ${context}`);
        }
    }

    async submitUpgradeRequest() {
        const textarea = document.querySelector('.upgrade-textarea');
        const request = textarea?.value?.trim();
        
        if (!request) {
            this.showNotification('Please describe your upgrade request', 'error');
            return;
        }

        this.showNotification('Processing upgrade request...');

        // Process upgrade with AGI
        try {
            const response = await this.agiEngines.processUpgradeRequest(request);
            this.addMessage('agent', `📈 **Upgrade Request Processed**\n\n${response.message}`);
            textarea.value = '';
            this.closeSettings();
        } catch (e) {
            this.showNotification(`Error processing upgrade: ${e.message}`, 'error');
        }
    }

    async addMCPServer() {
        const url = prompt('Enter MCP Server GitHub URL or documentation link:');
        if (!url) return;

        this.showNotification('Adding MCP server...');

        try {
            await this.mcpClient.addServer(url);
            this.showNotification('MCP server added successfully!');
        } catch (e) {
            this.showNotification(`Error adding MCP server: ${e.message}`, 'error');
        }
    }

    openRepoSelector() {
        document.getElementById('repo-search')?.focus();
    }

    showAGIBoards() {
        const boardSelect = document.getElementById('agi-board-select');
        if (boardSelect) {
            boardSelect.focus();
        }
    }

    showNotification(message, type = 'info') {
        // Simple notification - could be enhanced with a proper notification system
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // Show in status bar temporarily
        const statusItem = document.createElement('div');
        statusItem.className = 'status-item';
        statusItem.style.animation = 'fadeIn 0.3s';
        statusItem.innerHTML = `<i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i> ${message}`;
        
        const statusLeft = document.querySelector('.status-left');
        statusLeft?.appendChild(statusItem);
        
        setTimeout(() => {
            statusItem.remove();
        }, 3000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.omniCoder = new OmniCoderApp();
});
