CC ?= gcc
CFLAGS ?= -Wall -Wextra -O2

all: scheduler_demo

scheduler_demo: scheduler.c
	$(CC) $(CFLAGS) scheduler.c -o scheduler_demo

clean:
	rm -f scheduler_demo
