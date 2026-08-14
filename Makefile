.PHONY: up down logs migrate seed deploy

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python -m app.content.load

# Full stack including the Cloudflare Tunnel, then apply migrations and reload content.
deploy:
	git pull
	docker compose --profile tunnel up -d --build
	$(MAKE) migrate
	$(MAKE) seed
