# OmniCoder-AGI

> **The World's Most Advanced Coding Automation Agent CLI**

[![Quality](https://img.shields.io/badge/Quality-99.27%25-brightgreen)](https://github.com/pythpythpython/OmniCoder-AGI)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://python.org)

OmniCoder-AGI is a comprehensive CLI-based coding automation system that combines multiple AGI engines, MCP (Model Context Protocol) integrations, and advanced training/testing capabilities to provide the ultimate coding assistant experience.

## 🚀 Features

### Core Capabilities
- **Multi-Agent Execution**: Run multiple AGI engines on the same task and pick the best result
- **17 Specialized AGI Boards**: Code architecture, generation, review, testing, security, and more
- **10 Primary AGI Engines**: Trained to 99.27%+ quality with continuous improvement
- **12 MCP Integrations**: GitHub, TypeScript, Python, Java, Kotlin, C#, Go, PHP, Ruby, Rust, Swift

### Advanced Features
- **🎤 Voice Input**: Hands-free coding with speech recognition
- **🤝 Real-time Collaboration**: Team coding sessions
- **🧠 Continuous Learning**: Learns from every interaction
- **⚙️ Hyperparameter Tuning**: Auto-optimize engine performance
- **🔄 Self-Upgrade**: Automatic system improvements
- **🌐 Browser Extension**: Code assistance in your browser
- **📊 Comprehensive Tracking**: Full session history and analytics

### Training & Quality
- **100% Quality Target**: Continuous training toward perfect quality
- **Extreme Training Mode**: Maximum intensity training cycles
- **Test Verification**: Automated testing boards for all outputs
- **Quality Verification**: Code quality assurance boards

## 📦 Installation

### Quick Install
```bash
# Clone the repository
git clone https://github.com/pythpythpython/OmniCoder-AGI.git
cd OmniCoder-AGI

# Install with pip
pip install -e .
```

### With All Optional Dependencies
```bash
pip install -e ".[all]"
```

### Optional Extras
```bash
# Voice input support
pip install -e ".[voice]"

# Rich terminal output
pip install -e ".[rich]"

# Development tools
pip install -e ".[dev]"
```

## 🏁 Quick Start

### Initialize the System
```bash
python init_omnicoder.py
```

### Basic Usage
```bash
# Run a coding task
omnicoder-agi run "Create a REST API with authentication"

# Multi-agent task (3 agents collaborate)
omnicoder-agi multi "Build a todo app with React" --agents 3

# View AGI boards
omnicoder-agi boards

# View engines
omnicoder-agi engines

# View statistics
omnicoder-agi stats
```

### GitHub Integration
```bash
# Login with PAT token
omnicoder-agi github login --token YOUR_GITHUB_PAT

# Check status
omnicoder-agi github status

# List repositories
omnicoder-agi github repos

# Browse a repository
omnicoder-agi github browse --repo owner/repo
```

### Training & Tuning
```bash
# Run training cycle
omnicoder-agi train --intensity extreme

# Tune hyperparameters
omnicoder-agi tune --metrics response_quality,code_accuracy

# Run verification
omnicoder-agi verify "Check code quality"
```

### Self-Upgrade
```bash
# Plan an upgrade
omnicoder-agi upgrade "Add voice input support"

# Execute upgrade automatically
omnicoder-agi upgrade "Add new feature" --auto
```

### MCP Servers
```bash
# List MCP servers
omnicoder-agi mcp list

# Add custom MCP server
omnicoder-agi mcp add --url https://github.com/user/mcp-server.git

# Route a task to MCPs
omnicoder-agi mcp route --task "Build Python API" --language python
```

### Settings Management
```bash
# Show all settings
omnicoder-agi settings show

# Set a specific value
omnicoder-agi settings set --key agi.targetQuality --value 1.0

# Add API token
omnicoder-agi settings add-token --name openai --token YOUR_TOKEN
```

### Memory & History
```bash
# Save to memory
omnicoder-agi memory save --key project_info --data '{"name": "MyApp"}'

# Load from memory
omnicoder-agi memory load --key project_info

# View session history
omnicoder-agi history --target sessions --limit 20

# View training history
omnicoder-agi history --target learning
```

## 🤖 AGI Boards

| Board | Description | Primary Engine |
|-------|-------------|----------------|
| `code-architect` | High-level design and planning | PlanVoice-G4-G3-203 |
| `code-generator` | Feature implementation | ImprovePlan-G4-G3-172 |
| `code-reviewer` | Quality and security review | PerceiveRise-G4-G3-185 |
| `bug-detector` | Bug hunting and diagnostics | PerceiveRise-G4-G3-185 |
| `unit-testing` | Test generation | PerceiveRise-G4-G3-185 |
| `doc-generator` | Documentation generation | LinguaChart-G4-G3-192 |
| `security` | Security analysis | VirtueArchive-G4-G3-152 |
| `optimization` | Performance tuning | ImprovePlan-G4-G3-172 |
| `refactoring` | Code cleanup | EvolveChart-G4-G3-171 |
| `test-verifier` | Test verification | VirtueArchive-G4-G3-152 |
| `quality-verifier` | Quality verification | PerceiveRise-G4-G3-185 |
| `hyperparameter-tuner` | Engine optimization | ImprovePlan-G4-G3-172 |
| `continuous-learner` | Continuous learning | ImprovePlan-G4-G3-172 |

## 🔌 MCP Integrations

The following Model Context Protocol servers are supported:

- **GitHub** - Repository management, issues, PRs, actions
- **TypeScript** - Type analysis, transpilation, linting
- **Python** - Code analysis, testing, type checking
- **Java** - Maven/Gradle support, code analysis
- **Kotlin** - Coroutines, Android support
- **C#** - .NET and NuGet support
- **Go** - Modules, testing, benchmarking
- **PHP** - Composer support
- **Ruby** - Rails and gems support
- **Rust** - Cargo, memory safety analysis
- **Swift** - Xcode and iOS support
- **OpenStax** - Educational content

## 🎤 Voice Input

Enable voice input for hands-free coding:

```bash
# Install voice dependencies
pip install SpeechRecognition pyaudio

# Use voice input
omnicoder-agi run "your task" --voice
```

Voice commands:
- Say your task naturally
- "run [task]" - Execute a task
- "train" - Start training
- "upgrade" - Self-upgrade
- "stop" or "exit" - End voice mode

## 🌐 Browser Extension

Generate and use the browser extension:

```bash
# Generate extension files
python -m cli.browser_extension generate

# Start extension server
python -m cli.browser_extension
```

Install in Chrome:
1. Go to `chrome://extensions/`
2. Enable Developer mode
3. Click "Load unpacked"
4. Select the `browser_extension` directory

## 📊 Training Intensities

| Intensity | Description | Quality Boost |
|-----------|-------------|---------------|
| `low` | Light training | +0.01% |
| `medium` | Standard training | +0.05% |
| `high` | Intensive training | +0.10% |
| `extreme` | Maximum training | +0.50% |

## 🔧 Configuration

Settings are stored in `settings/default.json`:

```json
{
  "agi": {
    "defaultBoard": "auto",
    "multiAgentMode": true,
    "targetQuality": 1.0
  },
  "github": {
    "username": "your-username",
    "autoPushMerge": true
  },
  "training": {
    "defaultIntensity": "high",
    "autoTrain": true
  }
}
```

## 📁 Project Structure

```
OmniCoder-AGI/
├── cli/
│   ├── omnicoder_agi.py      # Main CLI
│   ├── voice_input.py        # Voice input module
│   ├── collaboration.py      # Collaboration features
│   ├── training_engine.py    # Advanced training
│   └── browser_extension.py  # Browser extension
├── _data/
│   └── agi_engines.yml       # Engine configurations
├── agi_boards/
│   └── boards_config.json    # Board configurations
├── mcp_integrations/
│   └── config.json           # MCP server configs
├── settings/
│   └── default.json          # Application settings
├── database/
│   ├── memory/               # Persistent memory
│   ├── sessions/             # Session logs
│   └── training/             # Training data
└── init_omnicoder.py         # Initialization script
```

## 🔐 Security

- PAT tokens are stored locally in settings
- Never commit tokens to version control
- Use environment variables for sensitive data:
  ```bash
  export GITHUB_PAT=your_token
  ```

## 📈 Roadmap

- [x] Core CLI with multi-agent support
- [x] GitHub integration
- [x] 12 MCP integrations
- [x] Training & hyperparameter tuning
- [x] Voice input support
- [x] Browser extension
- [x] Collaboration features
- [ ] 100% quality across all engines
- [ ] Custom AGI engine training
- [ ] Real-time streaming responses
- [ ] Plugin architecture

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 👤 Author

**pythpythpython**
- GitHub: [@pythpythpython](https://github.com/pythpythpython)
- Email: pyth.pyth.python@gmail.com

---

**OmniCoder-AGI** - *Coding at the speed of thought* 🚀
