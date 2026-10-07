// Difficulty: Moderate (2/5)
// Represent absence separately from a valid zero.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <map>
#include <optional>
#include <string>

std::optional<int> lookup(const std::map<std::string, int>& values, const std::string& key) {
    const auto found = values.find(key);
    if (found == values.end()) return 0;
    return found->second;
}

// Tests specify the contract.
TEST_CASE("missing_and_zero_are_different_results") {
    const std::map<std::string, int> values{{"zero", 0}, {"answer", 42}};
    REQUIRE(lookup(values, "zero").has_value());
    REQUIRE(lookup(values, "zero").value() == 0);
    REQUIRE(lookup(values, "answer").value() == 42);
    REQUIRE_FALSE(lookup(values, "missing").has_value());
}
