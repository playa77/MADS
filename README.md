# Multi-Agent Debate System

A simple Python framework for orchestrating AI-powered debates between multiple specialized agents. This system enables complex discussions on nuanced topics by having different AI personalities engage in structured conversations, each bringing unique perspectives and reasoning styles.

## Features

- **Multiple AI Personas**: Deploy up to 9 different agent types (Optimist, Pessimist, Pragmatist, Futurist, Historian, Contrarian, Strategist, Machiavelli, Stoic)
- **OpenRouter Integration**: Leverage various LLMs through OpenRouter's unified API
- **Interactive Mode**: Real-time human participation and moderation
- **Configurable Parameters**: Customizable debate rounds, temperature settings, and conversation flow
- **Smart Conversation Management**: History pruning, similarity detection, and graceful interruption handling
- **Rich Terminal Output**: Beautiful console formatting with progress indicators
- **JSON Logging**: Complete debate transcripts for analysis and review
- **Docker Support**: Containerized deployment for consistent environments

## Quick Start

### Prerequisites

- Python 3.8+
- OpenRouter API key ([get one here](https://openrouter.ai/))
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/multiagent-debate.git
   cd multiagent-debate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   # Create .env file
   echo "OPENROUTER_API_KEY=your_api_key_here" > .env
   ```

4. **Run your first debate:**
   ```bash
   python main.py --config config.json
   ```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker compose up --build

# For interactive sessions
docker compose run --service-ports debate
```

## Configuration

The system is highly configurable through `config.json`. Here's what each section controls:

### Model Configuration
```json
{
  "model": {
    "name": "deepseek/deepseek-chat-v3.1:free",
    "temperature": 0.6,
    "max_tokens": 512
  }
}
```

### Conversation Settings
```json
{
  "conversation": {
    "history_window_utts": 12,      // How many previous messages agents see
    "rounds": 50,                   // Maximum debate rounds
    "stop_on_repeat": 2,            // Stop if agent repeats similar responses
    "stop_on_user_input": true,     // Allow interactive interruption
    "seed_topic": "Your debate topic here",
    "query_delay_seconds": 5,       // Delay between API calls
    "repeat_similarity_threshold": 0.88  // Similarity threshold for repetition detection
  }
}
```

### Agent Personalities

Each agent has unique characteristics controlled by temperature and system prompts:

- **Optimist** (temp: 0.7) - Focuses on positive outcomes and opportunities
- **Pessimist** (temp: 0.4) - Highlights risks and potential downsides
- **Pragmatist** (temp: 0.3) - Emphasizes practical, implementable solutions
- **Futurist** (temp: 0.8) - Explores long-term implications and emerging trends
- **Historian** (temp: 0.5) - Provides historical context and precedents
- **Contrarian** (temp: 0.9) - Challenges assumptions and popular opinions
- **Strategist** (temp: 0.4) - Develops systematic approaches and frameworks
- **Machiavelli** (temp: 0.6) - Considers power dynamics and realpolitik
- **Stoic** (temp: 0.5) - Focuses on acceptance, resilience, and practical wisdom

## Usage Examples

### Basic Debate
```bash
python main.py --config config.json --rounds 10
```

### Non-Interactive Mode
```bash
python main.py --no-interactive --delay 3
```

### Custom Configuration
```bash
python main.py --config custom_config.json --rounds 25 --delay 2
```

### Interactive Controls

During debates, you can:
- Press **Enter** to continue to the next agent
- Type **`u:your message`** to inject your own contribution
- Type **`q`** to quit gracefully

## File Structure

```
multiagent-debate/
├── main.py                 # Main orchestrator
├── agents.py              # Agent definitions and model creation
├── utils.py               # Utility functions
├── config.json            # Main configuration file
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker deployment configuration
├── Dockerfile             # Container build instructions
├── roles/                 # Directory for agent system prompts
│   ├── optimist.txt
│   ├── pessimist.txt
│   └── ...
├── data/                  # Debate logs and outputs
│   └── debates.json
└── .env                   # Environment variables (create this)
```

## System Prompts

Agent personalities are defined in text files under the `roles/` directory. Each file contains detailed instructions that shape how that agent thinks and responds. You can customize these prompts to create entirely new personas or refine existing ones.

Example structure for `roles/optimist.txt`:
```
You are the Optimist in this debate. Your role is to:
- Highlight positive possibilities and opportunities
- Propose constructive solutions
- Maintain hope while being realistic
- Challenge overly pessimistic viewpoints
[... detailed personality instructions ...]
```

## Debate Logging

All debates are automatically logged to `data/debates.json` in newline-delimited JSON format:

```json
{"ts": "2025-01-15T10:30:00Z", "round": 1, "agent_id": "optimist", "agent_name": "Optimist", "content": "I believe AI advancement...", "model": "deepseek/deepseek-chat-v3.1:free"}
{"ts": "2025-01-15T10:30:15Z", "round": 1, "agent_id": "pessimist", "agent_name": "Pessimist", "content": "However, we must consider...", "model": "deepseek/deepseek-chat-v3.1:free"}
```

This format makes it easy to analyze debates programmatically or import into analysis tools.

## Advanced Features

### Similarity Detection
The system can automatically detect when agents start repeating themselves, preventing circular discussions:
```json
{
  "stop_on_repeat": 2,
  "repeat_similarity_threshold": 0.88
}
```

### Graceful Shutdown
Press `Ctrl+C` at any time to gracefully stop the debate while preserving all logs.

### Custom Models
Easily switch between different AI models by updating the model configuration:
```json
{
  "model": {
    "name": "anthropic/claude-3-haiku",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

### Per-Agent Temperature
Fine-tune each agent's creativity individually:
```json
{
  "agents": [
    {"id": "creative", "name": "Creative Thinker", "temperature": 0.9},
    {"id": "analytical", "name": "Analyst", "temperature": 0.3}
  ]
}
```

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure your `.env` file contains `OPENROUTER_API_KEY=your_key_here`
   - Check that the environment variable name matches your config

2. **Model Not Available**
   - Verify the model name in your config exists on OpenRouter
   - Some models may require credits or specific access

3. **Import Errors**
   - Install dependencies: `pip install -r requirements.txt`
   - For conda users: `conda install langchain langchain-openai`

4. **Rate Limiting**
   - Increase `query_delay_seconds` in your config
   - Consider using paid models for higher rate limits

### Debug Mode

Enable verbose logging by modifying the logging configuration in your config file or by examining the generated `debates.json` file for detailed interaction logs.

## Contributing

We welcome contributions! Areas where help is particularly appreciated:

- New agent personalities and system prompts
- Additional model integrations
- Analysis tools for debate transcripts
- Performance optimizations
- Documentation improvements

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [LangChain](https://langchain.com/) for LLM integration
- Powered by [OpenRouter](https://openrouter.ai/) for model access
- Uses [Rich](https://rich.readthedocs.io/) for beautiful terminal output

## Example Debate Topics

Try these thought-provoking topics to see the system in action:

- "Should AI development be globally regulated, and if so, how?"
- "Will remote work fundamentally change urban development patterns?"
- "Is universal basic income inevitable with advancing automation?"
- "How should society balance privacy with security in the digital age?"
- "What role should genetic engineering play in human enhancement?"

---

**Ready to start your first debate?** Run `python main.py` and watch AI personalities engage in sophisticated discussions!
