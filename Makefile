all: aofsync.bin

clean:
	rm -rf dist
	rm -rf *.build
	rm -rf *.dist
	rm -rf *.onefile-build
	rm -fv aofsync.bin

aofsync.bin: aofsync/__init__.py
	poetry run nuitka3 --onefile --standalone --no-deployment-flag=self-execution aofsync/__init__.py -o aofsync.bin

install: aofsync.bin
	install -m 0755 aofsync.bin /usr/bin/aofsync

build: aofsync/__init__.py
	poetry build
