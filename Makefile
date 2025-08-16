
run:
	uv run python main.py

test:
	uv run python -m pytest tests

build:
	docker build -t georot . 