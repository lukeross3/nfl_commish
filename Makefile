isort:
	isort .

black:
	black .

flake8:
	flake8 .

format: isort black flake8

test:
	coverage run --source=nfl_commish/ -m pytest tests/
	coverage report -m
	rm .coverage*