#!/bin/bash

# FastAPI Development with tmux (Server + Tests)
# This script starts both development server and continuous testing in tmux

SESSION_NAME="fastapi-dev"

echo "🚀 Starting FastAPI Development Environment with tmux..."

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux is not installed. Please install tmux first:"
    echo "  macOS: brew install tmux"
    echo "  Ubuntu: sudo apt-get install tmux"
    echo ""
    echo "Alternatively, run these manually in separate terminals:"
    echo "  Terminal 1: ./scripts/dev-server.sh"
    echo "  Terminal 2: ./scripts/dev-test.sh"
    exit 1
fi

# Kill existing session if it exists
tmux kill-session -t $SESSION_NAME 2>/dev/null

# Create new tmux session
echo "📱 Creating tmux session '$SESSION_NAME'..."

# Create session and first window for FastAPI server
tmux new-session -d -s $SESSION_NAME -n "server"

# Send commands to start the development server
tmux send-keys -t $SESSION_NAME:server "source .venv/bin/activate" C-m
tmux send-keys -t $SESSION_NAME:server "./scripts/dev-server.sh" C-m

# Create second window for continuous testing
tmux new-window -t $SESSION_NAME -n "tests"
tmux send-keys -t $SESSION_NAME:tests "source .venv/bin/activate" C-m
tmux send-keys -t $SESSION_NAME:tests "./scripts/dev-test.sh" C-m

# Create third window for general development
tmux new-window -t $SESSION_NAME -n "dev"
tmux send-keys -t $SESSION_NAME:dev "source .venv/bin/activate" C-m

# Select the first window
tmux select-window -t $SESSION_NAME:server

echo "✅ tmux session '$SESSION_NAME' created with 3 windows:"
echo "  - server: FastAPI development server with hot reload"
echo "  - tests:  Continuous testing with pytest-watch"
echo "  - dev:    General development terminal"
echo ""
echo "🎯 Attaching to tmux session..."
echo "💡 Use Ctrl+B then 0/1/2 to switch between windows"
echo "💡 Use Ctrl+B then d to detach (keeps running in background)"
echo "💡 Use 'tmux attach -t $SESSION_NAME' to reattach later"
echo ""

# Attach to the session
tmux attach-session -t $SESSION_NAME