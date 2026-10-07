// Difficulty: Easy (1/5)
// Read a const, noncopyable object without taking ownership.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"


struct Reading {
    int value;
    explicit Reading(int initial) : value(initial) {}
    Reading(const Reading&) = delete;
};
int read(Reading reading) { return reading.value; }

// Tests specify the contract.
TEST_CASE("borrow_reads_const_noncopyable_state") {
    const Reading reading{42};
    REQUIRE(read(reading) == 42);
    REQUIRE(reading.value == 42);
}
