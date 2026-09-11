CXX ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -fsyntax-only

SRCS := $(wildcard src/reechee/*.cpp)

all:
	$(CXX) $(CXXFLAGS) -I. $(SRCS)

%:
	$(CXX) $(CXXFLAGS) -I. src/reechee/$*.cpp
