.PHONY: help start start-all stop build up down logs shell ollama-serve ollama-pull clean run-local freellmapi-up freellmapi-down freellmapi-serve freellmapi-logs

help:
	@echo "JobMatch - Makefile"
	@echo "------------------"
	@echo "start         levanta toda la solucion (ollama + app)"
	@echo "start-all     levanta ollama + freellmapi + app"
	@echo "stop          detiene todo"
	@echo ""
	@echo "build         docker compose build"
	@echo "up            docker compose up -d (solo app)"
	@echo "down          docker compose down"
	@echo "logs          docker compose logs -f"
	@echo "shell         docker compose exec app bash"
	@echo "ollama-serve  check/start ollama serve on host"
	@echo "ollama-pull   ollama pull llama3.2:3b"
	@echo "run-local     streamlit run app.py (without Docker)"
	@echo "clean         down + remove orphans"
	@echo ""
	@echo "FreeLLMAPI (opcional):"
	@echo "freellmapi-up   start freellmapi service + app"
	@echo "freellmapi-down stop freellmapi"
	@echo "freellmapi-logs freellmapi logs"
	@echo "freellmapi-serve check freellmapi on :3001"

# ==================== all-in-one ====================
start:
	@echo "=== JobMatch: levantar solucion ==="
	@if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then \
		echo "[1/4] Iniciando ollama serve..."; \
		nohup ollama serve > /tmp/ollama.log 2>&1 & \
		sleep 2; \
	fi
	@echo "[2/4] Verificando modelo llama3.2:3b..."
	@if ! ollama list 2>/dev/null | grep -q "llama3.2:3b"; then \
		echo "  -> Descargando modelo (2GB)..."; \
		ollama pull llama3.2:3b; \
	fi
	@echo "[3/4] Construyendo imagen..."
	@docker compose build
	@echo "[4/4] Levantando app..."
	@docker compose up -d
	@echo ""
	@echo "  JobMatch -> http://localhost:8501"
	@echo "  LLM      -> Ollama (localhost:11434) · llama3.2:3b"

start-all:
	@echo "=== JobMatch: levantar solucion completa ==="
	@if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then \
		echo "[1/6] Iniciando ollama serve..."; \
		nohup ollama serve > /tmp/ollama.log 2>&1 & \
		sleep 2; \
	fi
	@echo "[2/6] Verificando modelo llama3.2:3b..."
	@if ! ollama list 2>/dev/null | grep -q "llama3.2:3b"; then \
		echo "  -> Descargando modelo (2GB)..."; \
		ollama pull llama3.2:3b; \
	fi
	@echo "[3/6] Preparando FreeLLMAPI..."
	@if [ ! -f .env ] || ! grep -q "^FREELLMAPI_ENCRYPTION_KEY=" .env || [ -z "$$(grep '^FREELLMAPI_ENCRYPTION_KEY=' .env | cut -d= -f2)" ]; then \
		echo "  -> Generando encryption key..."; \
		echo "FREELLMAPI_ENCRYPTION_KEY=$$(openssl rand -hex 32)" >> .env; \
	fi
	@echo "[4/6] Construyendo imagen..."
	@docker compose build
	@echo "[5/6] Levantando freellmapi..."
	@docker compose --profile freellmapi up -d freellmapi
	@echo "[6/6] Levantando app..."
	@docker compose up -d app
	@echo ""
	@echo "  JobMatch   -> http://localhost:8501"
	@echo "  FreeLLMAPI -> http://localhost:3001 (dashboard)"
	@echo "  Ollama     -> localhost:11434 · llama3.2:3b"
	@echo ""
	@echo "  Configuracion sugerida en .env para usar FreeLLMAPI:"
	@echo "    FREELLMAPI_API_KEY=<tu unified key del dashboard>"

stop:
	@echo "Deteniendo servicios..."
	@docker compose --profile freellmapi down 2>/dev/null; true
	@echo "  Todo detenido."

build:
	docker compose build

up:
	docker compose up -d
	@echo "-> http://localhost:8501"

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec app bash

ollama-serve:
	@if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then \
		echo "Ollama is running on host"; \
	else \
		echo "Starting ollama serve on host..."; \
		nohup ollama serve > /tmp/ollama.log 2>&1 & \
		echo "Ollama started in background"; \
	fi

ollama-pull:
	ollama pull llama3.2:3b

run-local:
	streamlit run app.py --server.address 0.0.0.0

freellmapi-up:
	@if [ -f .env ] && grep -q "^FREELLMAPI_ENCRYPTION_KEY" .env && [ -n "$$(grep '^FREELLMAPI_ENCRYPTION_KEY' .env | cut -d= -f2)" ]; then \
		echo "Starting app + freellmapi..."; \
	else \
		echo "Generating encryption key for freellmapi..."; \
		echo "FREELLMAPI_ENCRYPTION_KEY=$$(openssl rand -hex 32)" >> .env; \
	fi
	@echo ">>> Dashboard de FreeLLMAPI en http://localhost:3001"
	@echo ">>> Agrega tus API keys de proveedores en el dashboard"
	@echo ">>> Copia tu 'unified key' (freellmapi-...) y ponla en .env como LLM_API_KEY"
	@docker compose --profile freellmapi up -d
	@echo "-> JobMatch: http://localhost:8501 | FreeLLMAPI: http://localhost:3001"

freellmapi-down:
	docker compose --profile freellmapi down

freellmapi-logs:
	docker compose --profile freellmapi logs -f

freellmapi-serve:
	@if curl -s http://localhost:3001/v1/models > /dev/null 2>&1; then \
		echo "FreeLLMAPI is running on :3001"; \
	else \
		echo "FreeLLMAPI is NOT running. Run: make freellmapi-up"; \
	fi

clean:
	docker compose down --rmi all --volumes --remove-orphans