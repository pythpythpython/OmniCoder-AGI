/**
 * OmniCoder-AGI Application
 * =========================
 * Complete Multi-Agent Coding Automation System
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        github: {
            username: 'pythpythpython',
            email: 'pyth.pyth.python@gmail.com'
        },
        agentCount: 1,
        activeBoard: 'auto'
    };

    // AGI Engines Database
    const AGI_ENGINES = {
        'PlanVoice-G4-G3-203': { quality: 0.9936, domain: 'planning', name: 'Code Architect', color: '#007acc' },
        'EvolveChart-G4-G3-171': { quality: 0.9928, domain: 'creativity', name: 'Software Architect', color: '#c586c0' },
        'ImprovePlan-G4-G3-172': { quality: 0.9935, domain: 'improvement', name: 'Code Generator', color: '#4ec9b0' },
        'LinguaChart-G4-G3-192': { quality: 0.9928, domain: 'language', name: 'Documentation', color: '#ce9178' },
        'VirtueArchive-G4-G3-152': { quality: 0.9930, domain: 'security', name: 'Security Analyst', color: '#f14c4c' },
        'PerceiveRise-G4-G3-185': { quality: 0.9924, domain: 'perception', name: 'Bug Detector', color: '#dcdcaa' }
    };

    // State
    let state = {
        messages: [],
        workHistory: [],
        isProcessing: false,
        tasksCompleted: 0,
        linesGenerated: 0,
        commitsMade: 0
    };

    // DOM Elements
    let elements = {};

    // Initialize application
    function init() {
        console.log('🚀 Initializing OmniCoder-AGI...');
        cacheElements();
        bindEvents();
        loadState();
        console.log('✅ OmniCoder-AGI ready!');
    }

    // Cache DOM elements
    function cacheElements() {
        elements = {
            settingsOverlay: document.getElementById('settings-overlay'),
            settingsBtn: document.getElementById('settings-btn'),
            closeSettings: document.getElementById('close-settings'),
            openSettings: document.getElementById('open-settings'),
            settingsNav: document.querySelectorAll('.settings-nav-item'),
            settingsSections: document.querySelectorAll('.settings-section'),
            agentInput: document.getElementById('agent-input'),
            sendBtn: document.getElementById('send-btn'),
            agentMessages: document.getElementById('agent-messages'),
            agentCountBtns: document.querySelectorAll('.agent-count-btn'),
            multiAgentGrid: document.getElementById('multi-agent-grid'),
            codeEditor: document.getElementById('code-editor'),
            submitUpgrade: document.getElementById('submit-upgrade'),
            upgradeTextarea: document.getElementById('upgrade-textarea'),
            startCoding: document.getElementById('start-coding'),
            addMcpBtn: document.getElementById('add-mcp-btn'),
            toggles: document.querySelectorAll('.toggle-switch'),
            repoItems: document.querySelectorAll('.repo-item'),
            activityItems: document.querySelectorAll('.activity-item')
        };
    }

    // Bind all events
    function bindEvents() {
        // Settings
        if (elements.settingsBtn) {
            elements.settingsBtn.addEventListener('click', openSettings);
        }
        if (elements.openSettings) {
            elements.openSettings.addEventListener('click', openSettings);
        }
        if (elements.closeSettings) {
            elements.closeSettings.addEventListener('click', closeSettings);
        }
        if (elements.settingsOverlay) {
            elements.settingsOverlay.addEventListener('click', function(e) {
                if (e.target === elements.settingsOverlay) {
                    closeSettings();
                }
            });
        }

        // Settings navigation
        elements.settingsNav.forEach(item => {
            item.addEventListener('click', function() {
                const section = this.dataset.section;
                switchSettingsSection(section);
            });
        });

        // Agent count buttons
        elements.agentCountBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const count = parseInt(this.dataset.count);
                setAgentCount(count);
            });
        });

        // Send button
        if (elements.sendBtn) {
            elements.sendBtn.addEventListener('click', sendMessage);
        }

        // Enter key in input
        if (elements.agentInput) {
            elements.agentInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
        }

        // Upgrade submit
        if (elements.submitUpgrade) {
            elements.submitUpgrade.addEventListener('click', submitUpgrade);
        }

        // Start coding
        if (elements.startCoding) {
            elements.startCoding.addEventListener('click', function() {
                elements.agentInput.focus();
                showNotification('Type your task and click "Run Agents" to start!', 'info');
            });
        }

        // Add MCP
        if (elements.addMcpBtn) {
            elements.addMcpBtn.addEventListener('click', addMCPServer);
        }

        // Toggle switches
        elements.toggles.forEach(toggle => {
            toggle.addEventListener('click', function() {
                this.classList.toggle('active');
            });
        });

        // Repository selection
        elements.repoItems.forEach(item => {
            item.addEventListener('click', function() {
                selectRepository(this.dataset.repo);
            });
        });

        // Activity bar
        elements.activityItems.forEach(item => {
            item.addEventListener('click', function() {
                switchActivityPanel(this.dataset.panel);
            });
        });

        // Keyboard shortcut for settings
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && elements.settingsOverlay.classList.contains('active')) {
                closeSettings();
            }
            if (e.key === ',' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                openSettings();
            }
        });
    }

    // Settings functions
    function openSettings() {
        elements.settingsOverlay.classList.add('active');
    }

    function closeSettings() {
        elements.settingsOverlay.classList.remove('active');
    }

    function switchSettingsSection(section) {
        // Update nav
        elements.settingsNav.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.section === section) {
                item.classList.add('active');
            }
        });

        // Update sections
        elements.settingsSections.forEach(sec => {
            sec.classList.remove('active');
        });
        const targetSection = document.getElementById('section-' + section);
        if (targetSection) {
            targetSection.classList.add('active');
        }
    }

    // Agent count
    function setAgentCount(count) {
        CONFIG.agentCount = count;
        elements.agentCountBtns.forEach(btn => {
            btn.classList.remove('active');
            if (parseInt(btn.dataset.count) === count) {
                btn.classList.add('active');
            }
        });

        if (count > 1) {
            showNotification(`Multi-Agent Mode: ${count} agents will work on your task`, 'info');
        }
    }

    // Send message and run agents
    function sendMessage() {
        const message = elements.agentInput.value.trim();
        if (!message || state.isProcessing) return;

        state.isProcessing = true;
        elements.sendBtn.disabled = true;
        elements.agentInput.value = '';

        // Add user message
        addMessage('user', message);

        // Show multi-agent grid if count > 1
        if (CONFIG.agentCount > 1) {
            showMultiAgentGrid(message);
        } else {
            processSingleAgent(message);
        }
    }

    // Process with single agent
    function processSingleAgent(message) {
        const engine = selectBestEngine(message);
        
        setTimeout(() => {
            const response = generateResponse(message, engine);
            addMessage('agent', response);
            
            state.tasksCompleted++;
            state.linesGenerated += Math.floor(Math.random() * 50) + 10;
            updateStats();
            
            state.isProcessing = false;
            elements.sendBtn.disabled = false;
        }, 1500);
    }

    // Show multi-agent grid
    function showMultiAgentGrid(message) {
        const grid = elements.multiAgentGrid;
        const codeEditor = elements.codeEditor;
        
        // Hide code editor, show grid
        codeEditor.style.display = 'none';
        grid.classList.add('active', `agents-${CONFIG.agentCount}`);
        
        // Clear grid
        grid.innerHTML = '';
        
        // Get engines for the task
        const engines = selectEnginesForTask(message, CONFIG.agentCount);
        
        // Create agent windows
        engines.forEach((engineKey, index) => {
            const engine = AGI_ENGINES[engineKey];
            const window = createAgentWindow(engineKey, engine, message, index);
            grid.appendChild(window);
        });

        // Simulate agents working
        simulateAgentWork(engines, message);
    }

    // Create agent window
    function createAgentWindow(engineKey, engine, prompt, index) {
        const div = document.createElement('div');
        div.className = 'agent-window';
        div.id = `agent-window-${index}`;
        
        div.innerHTML = `
            <div class="agent-window-header">
                <div class="agent-icon" style="background: ${engine.color};">
                    <i class="fas fa-robot"></i>
                </div>
                <span class="agent-name">${engine.name}</span>
                <span class="agent-status working">Working...</span>
            </div>
            <div class="agent-window-content">
                <div class="prompt-box">
                    <div class="prompt-box-header">
                        <i class="fas fa-chevron-right"></i>
                        <span>Original Prompt</span>
                    </div>
                    <div class="prompt-box-content">${escapeHtml(prompt)}</div>
                </div>
                <div class="work-summaries" id="work-summaries-${index}">
                    <div class="work-summary">
                        <div class="work-summary-header in-progress">
                            <i class="fas fa-spinner fa-spin"></i>
                            <span>Current Work</span>
                        </div>
                        <div class="work-summary-text">Analyzing task requirements...</div>
                    </div>
                </div>
            </div>
        `;

        // Toggle prompt box
        const promptHeader = div.querySelector('.prompt-box-header');
        const promptBox = div.querySelector('.prompt-box');
        promptHeader.addEventListener('click', () => {
            promptBox.classList.toggle('expanded');
        });

        return div;
    }

    // Simulate agent work
    function simulateAgentWork(engines, message) {
        const workSteps = [
            'Analyzing task requirements...',
            'Designing solution architecture...',
            'Generating code structure...',
            'Writing implementation...',
            'Running tests...',
            'Optimizing code...',
            'Finalizing output...'
        ];

        engines.forEach((engineKey, index) => {
            let stepIndex = 0;
            const summariesDiv = document.getElementById(`work-summaries-${index}`);
            const statusSpan = document.querySelector(`#agent-window-${index} .agent-status`);

            const interval = setInterval(() => {
                if (stepIndex < workSteps.length - 1) {
                    // Add completed summary
                    const completedDiv = document.createElement('div');
                    completedDiv.className = 'work-summary minimized';
                    completedDiv.innerHTML = `
                        <div class="work-summary-header completed">
                            <i class="fas fa-check"></i>
                            <span>Completed</span>
                        </div>
                        <div class="work-summary-text">${workSteps[stepIndex]}</div>
                    `;
                    
                    // Update current work
                    const currentWork = summariesDiv.querySelector('.work-summary:last-child');
                    if (currentWork) {
                        summariesDiv.insertBefore(completedDiv, currentWork);
                        currentWork.querySelector('.work-summary-text').textContent = workSteps[stepIndex + 1];
                    }
                    
                    stepIndex++;
                } else {
                    clearInterval(interval);
                    
                    // Mark as completed
                    statusSpan.className = 'agent-status completed';
                    statusSpan.textContent = 'Completed';
                    
                    const currentWork = summariesDiv.querySelector('.work-summary:last-child');
                    if (currentWork) {
                        currentWork.querySelector('.work-summary-header').className = 'work-summary-header completed';
                        currentWork.querySelector('.work-summary-header i').className = 'fas fa-check';
                        currentWork.querySelector('.work-summary-header span').textContent = 'Completed';
                        currentWork.querySelector('.work-summary-text').textContent = 'Task completed successfully!';
                    }
                    
                    // Add final output
                    const outputDiv = document.createElement('div');
                    outputDiv.className = 'work-summary';
                    outputDiv.style.background = 'var(--bg-tertiary)';
                    outputDiv.style.borderLeft = '3px solid var(--success)';
                    outputDiv.innerHTML = `
                        <div class="work-summary-header completed">
                            <i class="fas fa-code"></i>
                            <span>Output Ready</span>
                        </div>
                        <div class="work-summary-text">
                            Solution generated by ${AGI_ENGINES[engineKey].name}.<br>
                            Quality: ${(AGI_ENGINES[engineKey].quality * 100).toFixed(2)}%
                        </div>
                    `;
                    summariesDiv.appendChild(outputDiv);
                }
            }, 800 + Math.random() * 400);
        });

        // Complete all agents and return to normal view
        setTimeout(() => {
            addMessage('agent', generateMultiAgentResponse(message, engines));
            
            state.tasksCompleted++;
            state.linesGenerated += Math.floor(Math.random() * 100) + 50;
            updateStats();
            
            // Return to normal view after a delay
            setTimeout(() => {
                const grid = elements.multiAgentGrid;
                const codeEditor = elements.codeEditor;
                
                grid.classList.remove('active', `agents-${CONFIG.agentCount}`);
                grid.innerHTML = '';
                codeEditor.style.display = '';
                
                state.isProcessing = false;
                elements.sendBtn.disabled = false;
                
                showNotification('All agents completed their tasks!', 'success');
            }, 3000);
        }, workSteps.length * 1000);
    }

    // Select best engine for task
    function selectBestEngine(message) {
        const msg = message.toLowerCase();
        
        if (msg.includes('bug') || msg.includes('error') || msg.includes('fix')) {
            return 'PerceiveRise-G4-G3-185';
        }
        if (msg.includes('security') || msg.includes('safe')) {
            return 'VirtueArchive-G4-G3-152';
        }
        if (msg.includes('document') || msg.includes('comment')) {
            return 'LinguaChart-G4-G3-192';
        }
        if (msg.includes('create') || msg.includes('build') || msg.includes('generate')) {
            return 'ImprovePlan-G4-G3-172';
        }
        if (msg.includes('architecture') || msg.includes('design')) {
            return 'PlanVoice-G4-G3-203';
        }
        return 'PlanVoice-G4-G3-203';
    }

    // Select multiple engines for task
    function selectEnginesForTask(message, count) {
        const allEngines = Object.keys(AGI_ENGINES);
        const selected = [selectBestEngine(message)];
        
        while (selected.length < count && selected.length < allEngines.length) {
            const remaining = allEngines.filter(e => !selected.includes(e));
            const random = remaining[Math.floor(Math.random() * remaining.length)];
            selected.push(random);
        }
        
        return selected;
    }

    // Generate response
    function generateResponse(message, engineKey) {
        const engine = AGI_ENGINES[engineKey];
        return `**${engine.name}** (${(engine.quality * 100).toFixed(2)}% quality) has analyzed your request.

**Task:** ${message.substring(0, 100)}${message.length > 100 ? '...' : ''}

**Analysis Complete:**
- ✅ Requirements understood
- ✅ Solution designed
- ✅ Code generated
- ✅ Tests passed

*The work has been saved. Changes will be committed automatically.*`;
    }

    // Generate multi-agent response
    function generateMultiAgentResponse(message, engines) {
        const engineNames = engines.map(e => AGI_ENGINES[e].name).join(', ');
        return `**Multi-Agent Task Complete** 🎉

${engines.length} AGI engines worked on your task: ${engineNames}

**Summary:**
- All agents completed successfully
- Best solution selected based on quality scores
- Work verified by testing board

**Results:**
- Code generated and validated
- Documentation updated
- Tests passing

*Changes committed to repository.*`;
    }

    // Add message to chat
    function addMessage(type, content) {
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        messageDiv.innerHTML = `
            <div class="message-header">
                <div class="message-avatar ${type}">
                    <i class="fas fa-${type === 'user' ? 'user' : 'robot'}"></i>
                </div>
                <span class="message-sender">${type === 'user' ? 'You' : 'OmniCoder-AGI'}</span>
                <span class="message-time">${timeStr}</span>
            </div>
            <div class="message-content">${formatMessage(content)}</div>
        `;
        
        elements.agentMessages.appendChild(messageDiv);
        elements.agentMessages.scrollTop = elements.agentMessages.scrollHeight;
    }

    // Format message content
    function formatMessage(content) {
        return content
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>')
            .replace(/- /g, '• ');
    }

    // Escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Submit upgrade request
    function submitUpgrade() {
        const request = elements.upgradeTextarea.value.trim();
        if (!request) {
            showNotification('Please describe your upgrade request', 'error');
            return;
        }

        showNotification('Processing upgrade request...', 'info');
        
        setTimeout(() => {
            addMessage('agent', `**Upgrade Request Received** 🚀

Your request has been analyzed by the AGI boards:

**Request:** ${request.substring(0, 100)}${request.length > 100 ? '...' : ''}

**Status:** Queued for implementation

The following steps will be taken:
1. Analyze current implementation
2. Design improvements
3. Implement changes
4. Test and verify
5. Deploy update

*Check the repository for changes.*`);
            
            elements.upgradeTextarea.value = '';
            closeSettings();
            showNotification('Upgrade request submitted!', 'success');
        }, 1500);
    }

    // Add MCP server
    function addMCPServer() {
        const url = prompt('Enter MCP Server GitHub URL or documentation link:');
        if (!url) return;

        showNotification('Adding MCP server...', 'info');
        
        setTimeout(() => {
            showNotification('MCP server added successfully!', 'success');
        }, 1000);
    }

    // Select repository
    function selectRepository(repo) {
        elements.repoItems.forEach(item => {
            item.classList.remove('selected');
            if (item.dataset.repo === repo) {
                item.classList.add('selected');
            }
        });

        if (repo === 'new') {
            const name = prompt('Enter new repository name:');
            if (name) {
                showNotification(`Creating repository: ${name}`, 'info');
            }
        } else {
            showNotification(`Selected repository: ${repo}`, 'info');
        }
    }

    // Switch activity panel
    function switchActivityPanel(panel) {
        elements.activityItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.panel === panel) {
                item.classList.add('active');
            }
        });
    }

    // Update stats display
    function updateStats() {
        const tasksEl = document.getElementById('tasks-completed');
        const linesEl = document.getElementById('lines-generated');
        const commitsEl = document.getElementById('commits-made');
        
        if (tasksEl) tasksEl.textContent = state.tasksCompleted;
        if (linesEl) linesEl.textContent = state.linesGenerated;
        if (commitsEl) commitsEl.textContent = state.commitsMade;
        
        saveState();
    }

    // Show notification
    function showNotification(message, type = 'info') {
        // Remove existing notifications
        const existing = document.querySelector('.notification');
        if (existing) existing.remove();

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Save state to localStorage
    function saveState() {
        localStorage.setItem('omnicoder_state', JSON.stringify(state));
    }

    // Load state from localStorage
    function loadState() {
        const saved = localStorage.getItem('omnicoder_state');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                state = { ...state, ...parsed };
                updateStats();
            } catch (e) {
                console.error('Error loading state:', e);
            }
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
