CXX ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -fsyntax-only

all:
	find src generated -name '*.cpp' -exec $(CXX) $(CXXFLAGS) -I. -Isrc/bestsofar {} +
