.PHONY: clean up demo down logs test

clean:
	docker compose down -v --remove-orphans
	rm -rf artifacts/release
	mkdir -p artifacts/release

up:
	docker compose up --build -d

demo:
	docker compose down -v --remove-orphans
	mkdir -p artifacts/release
	sh scripts/run_demo.sh

down:
	docker compose down

logs:
	docker compose logs attacker
	docker compose logs web
	docker compose logs db

test:
	pytest -q