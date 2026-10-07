#pragma once
#include <catch2/catch_test_macros.hpp>
#include <memory>

// Observable resource lifetime; counts are accessed only by the calling thread.
struct Tracked {
    static inline int live = 0;
    static inline int destroyed = 0;
    int value;
    explicit Tracked(int initial) : value(initial) { ++live; }
    Tracked(const Tracked&) = delete;
    Tracked& operator=(const Tracked&) = delete;
    ~Tracked() { --live; ++destroyed; }
};
