.PHONY: build test clean

build:
	python3 script/build.py

test:
	python3 -m pytest test/

clean:
	rm -rf site/
