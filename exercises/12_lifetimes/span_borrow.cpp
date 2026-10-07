// Difficulty: Intermediate (3/5)
// Use a span to mutate original array or vector elements.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <array>
#include <span>
#include <vector>

void double_values(std::span<int> values) {
    for (auto value : values)
        value *= 2;
}

// Tests specify the contract.
TEST_CASE("span_mutation_reaches_both_storage_types") {
    std::array<int, 3> array{1, 0, -2};
    double_values(array);
    REQUIRE(array[0] == 2);
    REQUIRE(array[1] == 0);
    REQUIRE(array[2] == -4);
    std::vector<int> vector{3, 4};
    double_values(vector);
    REQUIRE(vector == std::vector<int>{6, 8});
    double_values(std::span<int>{});
}
