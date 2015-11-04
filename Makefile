
all:

test:
	py.test --cov=onagame2015 --cov-report term-missing tests

clean:
	find . -type f -name "*.pyc" -delete
