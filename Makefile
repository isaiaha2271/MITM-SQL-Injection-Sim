bootstrap:
	mkdir -p web
	mkdir -p db
	mkdir -p attacker
	touch web/app.py
	touch web/Dockerfile
up:
	docker compose up --build -d

demo:
	mkdir -p artifacts/release
	sh scripts/run_demo.sh

down:
	docker compose down

logs:
	docker compose logs attacker

test:
	pytest -q