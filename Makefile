isort:
	isort .

black:
	black .

flake8:
	flake8 .

format: isort black flake8

test-small:
	coverage run --source=nfl_commish/ -m pytest tests/small/
	coverage report -m
	rm .coverage*

test-large:
	coverage run --source=nfl_commish/ -m pytest tests/large/
	coverage report -m
	rm .coverage*

test-all:
	coverage run --source=nfl_commish/ -m pytest tests/small/ tests/large/
	coverage report -m
	rm .coverage*