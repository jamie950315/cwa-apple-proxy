test:
	./scripts/test.sh

verify:
	python3 scripts/verify_repo.py

bootstrap:
	./scripts/bootstrap-dev.sh

status:
	./scripts/pi-status.sh
