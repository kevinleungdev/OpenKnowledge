export CORS_ALLOW_ORIGIN="http://localhost:5173;http://localhost:8080"
PORT="${PORT:-8080}"
#uvicorn open_knowledge.main:app --port $PORT --host 0.0.0.0 --forwarded-allow-ips '*' --reload
uvicorn open_knowledge.main:app