all: cpp py

cpp:
	$(MAKE) -C cpp/bc2024
	$(MAKE) -C cpp/bc2025
	$(MAKE) -C cpp/bc2026

py:
	find py -name '*.py' -exec python3 -m py_compile {} +

.PHONY: all cpp py
