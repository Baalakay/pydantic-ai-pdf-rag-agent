#!/bin/bash
docker compose stop ollama
docker compose rm -f ollama
docker volume rm ollama_data || true
docker compose up -d ollama --no-deps
