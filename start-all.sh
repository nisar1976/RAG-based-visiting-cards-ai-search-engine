#!/bin/bash
cd /c/Users/Nisar/Desktop/AI_chatbot_visitingcards

echo "Starting Backend Server on port 8000..."
/c/Users/Nisar/Desktop/AI_chatbot_visitingcards/.venv/Scripts/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

sleep 3

echo "Starting Frontend Server on port 3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

wait
