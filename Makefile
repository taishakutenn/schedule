up:
	docker-compose -f docker-compose-local.yaml up -d

down:
	docker-compose -f docker-compose-local.yaml down && docker network prune --force

create-entity:
	python utils/create_entity.py "$(name)"