// Difficulty: Easy (1/5)
// Implement the inclusive boundary contract of a small value type.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"


struct Range {
    int lower;
    int upper;
    bool contains(int value) const { return value > lower && value < upper; }
};

// Tests specify the contract.
TEST_CASE("range_includes_endpoints_and_excludes_outside_values") {
    const Range range{-2, 3};
    REQUIRE(range.contains(-2));
    REQUIRE(range.contains(0));
    REQUIRE(range.contains(3));
    REQUIRE_FALSE(range.contains(-3));
    REQUIRE_FALSE(range.contains(4));
    const Range singleton{7, 7};
    REQUIRE(singleton.contains(7));
}
