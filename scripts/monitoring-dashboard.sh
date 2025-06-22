#!/bin/bash

# Script to manage Kubernetes port-forwarding for monitoring dashboard

NAMESPACE="monitoring"
SERVICE="prometheus-stack-grafana"
LOCAL_PORT="3030"
REMOTE_PORT="80"
LOG_FILE="/tmp/grafana-port-forward.log"
PID_FILE="/tmp/grafana-port-forward.pid"

# Function to start port-forwarding
start_port_forward() {
    # Check if port-forward is already running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "Port-forwarding is already running with PID $PID"
            echo "Access Grafana at http://localhost:$LOCAL_PORT"
            return 0
        else
            echo "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi

    # Start port-forwarding in background
    echo "Starting port-forwarding for $SERVICE in namespace $NAMESPACE..."
    nohup kubectl port-forward -n "$NAMESPACE" svc/"$SERVICE" "$LOCAL_PORT":"$REMOTE_PORT" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    # Wait a moment to ensure it's running
    sleep 2

    # Check if port-forward is running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "Port-forwarding started successfully with PID $PID"
            echo "Access Grafana at http://localhost:$LOCAL_PORT"
            echo "Logs available at $LOG_FILE"
        else
            echo "Failed to start port-forwarding"
            cat "$LOG_FILE"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo "Failed to create PID file"
        return 1
    fi
}

# Function to stop port-forwarding
stop_port_forward() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "Stopping port-forwarding process with PID $PID..."
            kill $PID
            rm -f "$PID_FILE"
            echo "Port-forwarding stopped"
        else
            echo "No active port-forwarding process found, but PID file exists"
            rm -f "$PID_FILE"
        fi
    else
        echo "No port-forwarding process found"
    fi
}

# Function to check status
status_port_forward() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "Port-forwarding is running with PID $PID"
            echo "Access Grafana at http://localhost:$LOCAL_PORT"
            echo "Logs available at $LOG_FILE"
        else
            echo "No active port-forwarding process found, but PID file exists"
            echo "You may want to run: $0 clean"
        fi
    else
        echo "No port-forwarding process found"
    fi
}

# Function to clean up stale PID files
clean_port_forward() {
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
        echo "Removed stale PID file"
    fi
    echo "Clean up complete"
}

# Function to display help
show_help() {
    echo "Usage: $0 [start|stop|status|clean|help]"
    echo
    echo "Commands:"
    echo "  start   - Start port-forwarding in the background"
    echo "  stop    - Stop port-forwarding"
    echo "  status  - Check if port-forwarding is running"
    echo "  clean   - Clean up stale PID files"
    echo "  help    - Show this help message"
}

# Main script logic
case "$1" in
    start)
        start_port_forward
        ;;
    stop)
        stop_port_forward
        ;;
    status)
        status_port_forward
        ;;
    clean)
        clean_port_forward
        ;;
    help|*)
        show_help
        ;;
esac

exit 0
