// Difficulty: Moderate (2/5)
// Express a counting contract with a predicate, including zero.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <algorithm>
#include <vector>

auto count_nonnegative(const std::vector<int> &values) {
    return std::count_if(values.begin(), values.end(), [](int value) { return value > 0; });
}

// Tests specify the contract.
TEST_CASE("predicate_handles_mixed_empty_and_boundary_inputs") {
    REQUIRE(count_nonnegative({-2, 0, 3, 0}) == 3);
    REQUIRE(count_nonnegative({}) == 0);
    REQUIRE(count_nonnegative({-1, -2}) == 0);
    REQUIRE(count_nonnegative({0}) == 1);
}
