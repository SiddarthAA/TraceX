#!/bin/bash

# TraceX Launcher Script
# Provides easy access to both CLI and Web UI

show_help() {
    cat << EOF
🔗 TraceX - HLR-LLR Traceability System

Usage: ./run.sh [command] [options]

Commands:
    ui              Launch Streamlit web interface (default)
    cli             Run command-line interface (see tracex_cli.py --help)
    test            Run system tests
    samples         Generate sample data files
    setup           Initial setup (API keys)
    help            Show this help message

Examples:
    ./run.sh                          # Launch web UI
    ./run.sh ui                       # Launch web UI
    ./run.sh cli --sample             # CLI with sample data
    ./run.sh test                     # Run tests
    ./run.sh samples                  # Generate sample files
    ./run.sh setup                    # Setup wizard

For CLI help:
    ./run.sh cli --help

EOF
}

case "${1:-ui}" in
    ui)
        echo "🔗 Starting TraceX Web UI..."
        echo ""
        echo "Opening Streamlit interface..."
        echo "Default URL: http://localhost:8501"
        echo ""
        uv run streamlit run app.py
        ;;
    
    cli)
        shift  # Remove 'cli' from arguments
        uv run python tracex_cli.py run "$@"
        ;;
    
    test)
        echo "🧪 Running TraceX System Tests..."
        uv run python tests/test_system.py
        ;;
    
    samples)
        echo "📦 Generating Sample Data..."
        uv run python scripts/generate_samples.py
        ;;
    
    setup)
        echo "⚙️  TraceX Setup Wizard"
        echo ""
        
        if [ -f .env ]; then
            echo "⚠️  .env file already exists"
            read -p "Overwrite? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Setup cancelled"
                exit 0
            fi
        fi
        
        cp config/.env.example .env
        echo "✅ Created .env file"
        echo ""
        echo "Please edit .env and add your API keys:"
        echo "  nano .env"
        echo ""
        echo "API Key Sources:"
        echo "  Gemini:  https://aistudio.google.com/apikey"
        echo "  Claude:  https://console.anthropic.com/"
        echo "  OpenAI:  https://platform.openai.com/"
        echo "  Groq:    https://console.groq.com/"
        echo ""
        echo "For local models (no API key):"
        echo "  Install Ollama: curl -fsSL https://ollama.com/install.sh | sh"
        echo "  Start Ollama: ollama serve"
        echo "  Pull a model: ollama pull llama3.2"
        ;;
    
    help|--help|-h)
        show_help
        ;;
    
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

