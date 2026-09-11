CXX ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -fsyntax-only

all:
	find src -name '*.cpp' -exec $(CXX) $(CXXFLAGS) -I. -Isrc/philip_06 {} +
