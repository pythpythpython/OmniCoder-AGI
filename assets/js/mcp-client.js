/**
 * OmniCoder-AGI MCP Client
 * ========================
 * Model Context Protocol integration for multiple SDKs
 */

class MCPClient {
    constructor(app) {
        this.app = app;
        
        // Available MCP servers
        this.servers = {
            github: {
                name: 'GitHub MCP Server',
                repo: 'github/github-mcp-server',
                status: 'connected',
                capabilities: ['repos', 'issues', 'prs', 'commits', 'branches', 'actions'],
                icon: 'fab fa-github'
            },
            typescript: {
                name: 'TypeScript SDK',
                repo: 'modelcontextprotocol/typescript-sdk',
                status: 'connected',
                capabilities: ['ts-analysis', 'type-checking', 'transpilation'],
                icon: 'fab fa-js'
            },
            python: {
                name: 'Python SDK',
                repo: 'modelcontextprotocol/python-sdk',
                status: 'connected',
                capabilities: ['py-analysis', 'linting', 'testing'],
                icon: 'fab fa-python'
            },
            java: {
                name: 'Java SDK',
                repo: 'modelcontextprotocol/java-sdk',
                status: 'connected',
                capabilities: ['java-analysis', 'maven', 'gradle'],
                icon: 'fab fa-java'
            },
            kotlin: {
                name: 'Kotlin SDK',
                repo: 'modelcontextprotocol/kotlin-sdk',
                status: 'connected',
                capabilities: ['kotlin-analysis', 'coroutines'],
                icon: 'fas fa-k'
            },
            csharp: {
                name: 'C# SDK',
                repo: 'modelcontextprotocol/csharp-sdk',
                status: 'connected',
                capabilities: ['csharp-analysis', 'dotnet'],
                icon: 'fas fa-hashtag'
            },
            go: {
                name: 'Go SDK',
                repo: 'modelcontextprotocol/go-sdk',
                status: 'connected',
                capabilities: ['go-analysis', 'modules'],
                icon: 'fab fa-golang'
            },
            php: {
                name: 'PHP SDK',
                repo: 'modelcontextprotocol/php-sdk',
                status: 'connected',
                capabilities: ['php-analysis', 'composer'],
                icon: 'fab fa-php'
            },
            ruby: {
                name: 'Ruby SDK',
                repo: 'modelcontextprotocol/ruby-sdk',
                status: 'connected',
                capabilities: ['ruby-analysis', 'gems', 'rails'],
                icon: 'fas fa-gem'
            },
            rust: {
                name: 'Rust SDK',
                repo: 'modelcontextprotocol/rust-sdk',
                status: 'connected',
                capabilities: ['rust-analysis', 'cargo', 'memory-safety'],
                icon: 'fab fa-rust'
            },
            swift: {
                name: 'Swift SDK',
                repo: 'modelcontextprotocol/swift-sdk',
                status: 'connected',
                capabilities: ['swift-analysis', 'xcode', 'ios'],
                icon: 'fab fa-swift'
            },
            openstax: {
                name: 'OpenStax MCP',
                repo: 'pythpythpython/openstax-mcp-server',
                status: 'connected',
                capabilities: ['education', 'textbooks', 'learning'],
                icon: 'fas fa-book'
            }
        };

        // MCP routing based on task type
        this.routing = {
            frontend: ['typescript', 'github'],
            backend: ['python', 'go', 'java', 'github'],
            mobile: ['swift', 'kotlin', 'github'],
            systems: ['rust', 'go', 'csharp', 'github'],
            web: ['php', 'ruby', 'typescript', 'github'],
            research: ['openstax', 'github'],
            general: ['github', 'typescript', 'python']
        };

        this.activeConnections = new Map();
        this.requestQueue = [];
    }

    /**
     * Get list of all available MCP servers
     */
    getServers() {
        return Object.entries(this.servers).map(([id, server]) => ({
            id,
            ...server
        }));
    }

    /**
     * Get servers by capability
     */
    getServersByCapability(capability) {
        return Object.entries(this.servers)
            .filter(([_, server]) => server.capabilities.includes(capability))
            .map(([id, server]) => ({ id, ...server }));
    }

    /**
     * Route request to appropriate MCP servers
     */
    routeRequest(taskType, context = {}) {
        const servers = this.routing[taskType] || this.routing.general;
        
        // Select optimal servers based on context
        const selectedServers = servers.filter(serverId => {
            const server = this.servers[serverId];
            return server && server.status === 'connected';
        });

        return selectedServers.map(id => ({
            id,
            ...this.servers[id]
        }));
    }

    /**
     * Execute request across MCP servers
     */
    async executeRequest(request, options = {}) {
        const { servers = [], priority = 'normal' } = options;
        
        const targetServers = servers.length > 0 
            ? servers.map(id => ({ id, ...this.servers[id] }))
            : this.routeRequest(request.taskType);

        const results = await Promise.allSettled(
            targetServers.map(server => this.callServer(server.id, request))
        );

        return {
            success: results.filter(r => r.status === 'fulfilled').length,
            failed: results.filter(r => r.status === 'rejected').length,
            results: results.map((r, i) => ({
                server: targetServers[i].id,
                status: r.status,
                data: r.status === 'fulfilled' ? r.value : r.reason
            }))
        };
    }

    /**
     * Call a specific MCP server
     */
    async callServer(serverId, request) {
        const server = this.servers[serverId];
        if (!server) {
            throw new Error(`Server ${serverId} not found`);
        }

        if (server.status !== 'connected') {
            throw new Error(`Server ${serverId} not connected`);
        }

        // Simulate MCP call - in production this would make actual API calls
        console.log(`📡 Calling MCP server: ${server.name}`);
        
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    server: serverId,
                    request: request,
                    response: {
                        status: 'success',
                        data: `Response from ${server.name}`
                    }
                });
            }, 100);
        });
    }

    /**
     * Add a new MCP server
     */
    async addServer(url) {
        console.log(`📥 Adding MCP server from: ${url}`);
        
        // Parse URL to extract server info
        const serverInfo = this.parseServerUrl(url);
        
        // Generate unique ID
        const serverId = serverInfo.name.toLowerCase().replace(/[^a-z0-9]/g, '-');
        
        // Add to servers
        this.servers[serverId] = {
            name: serverInfo.name,
            repo: serverInfo.repo,
            status: 'connecting',
            capabilities: serverInfo.capabilities || ['custom'],
            icon: 'fas fa-plug',
            custom: true
        };

        // Simulate connection
        await this.connectServer(serverId);
        
        return { id: serverId, ...this.servers[serverId] };
    }

    /**
     * Parse server URL to extract info
     */
    parseServerUrl(url) {
        // Handle GitHub URLs
        const githubMatch = url.match(/github\.com\/([^\/]+)\/([^\/]+)/);
        if (githubMatch) {
            return {
                name: githubMatch[2].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                repo: `${githubMatch[1]}/${githubMatch[2]}`,
                capabilities: ['custom']
            };
        }

        // Handle other URLs
        return {
            name: 'Custom MCP Server',
            repo: url,
            capabilities: ['custom']
        };
    }

    /**
     * Connect to a server
     */
    async connectServer(serverId) {
        const server = this.servers[serverId];
        if (!server) return false;

        console.log(`🔌 Connecting to ${server.name}...`);
        
        // Simulate connection process
        await new Promise(resolve => setTimeout(resolve, 500));
        
        server.status = 'connected';
        console.log(`✅ Connected to ${server.name}`);
        
        return true;
    }

    /**
     * Disconnect from a server
     */
    async disconnectServer(serverId) {
        const server = this.servers[serverId];
        if (!server) return false;

        console.log(`🔌 Disconnecting from ${server.name}...`);
        server.status = 'disconnected';
        
        return true;
    }

    /**
     * Get server statistics
     */
    getStatistics() {
        const total = Object.keys(this.servers).length;
        const connected = Object.values(this.servers).filter(s => s.status === 'connected').length;
        const capabilities = new Set();
        
        Object.values(this.servers).forEach(s => {
            s.capabilities.forEach(c => capabilities.add(c));
        });

        return {
            totalServers: total,
            connectedServers: connected,
            disconnectedServers: total - connected,
            totalCapabilities: capabilities.size,
            capabilities: Array.from(capabilities)
        };
    }

    /**
     * Select optimal MCPs for a coding task
     */
    selectOptimalMCPs(task, context = {}) {
        const taskLower = task.toLowerCase();
        const selected = [];

        // Always include GitHub for repo operations
        if (this.servers.github?.status === 'connected') {
            selected.push('github');
        }

        // Language-specific selection
        if (taskLower.includes('typescript') || taskLower.includes('javascript') || taskLower.includes('react')) {
            selected.push('typescript');
        }
        if (taskLower.includes('python') || taskLower.includes('django') || taskLower.includes('flask')) {
            selected.push('python');
        }
        if (taskLower.includes('java') || taskLower.includes('spring')) {
            selected.push('java');
        }
        if (taskLower.includes('kotlin') || taskLower.includes('android')) {
            selected.push('kotlin');
        }
        if (taskLower.includes('c#') || taskLower.includes('csharp') || taskLower.includes('.net')) {
            selected.push('csharp');
        }
        if (taskLower.includes('go') || taskLower.includes('golang')) {
            selected.push('go');
        }
        if (taskLower.includes('php') || taskLower.includes('laravel')) {
            selected.push('php');
        }
        if (taskLower.includes('ruby') || taskLower.includes('rails')) {
            selected.push('ruby');
        }
        if (taskLower.includes('rust')) {
            selected.push('rust');
        }
        if (taskLower.includes('swift') || taskLower.includes('ios')) {
            selected.push('swift');
        }
        if (taskLower.includes('learn') || taskLower.includes('education') || taskLower.includes('study')) {
            selected.push('openstax');
        }

        // Default to general MCPs if nothing specific
        if (selected.length <= 1) {
            selected.push('typescript', 'python');
        }

        return [...new Set(selected)].filter(id => this.servers[id]?.status === 'connected');
    }
}

// Export for use in main app
window.MCPClient = MCPClient;
