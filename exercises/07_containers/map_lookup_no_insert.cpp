// Difficulty: Easy (1/5)
// Look up a value without inserting a missing key.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <map>
#include <string>

int read_or_zero(std::map<std::string, int> &values, const std::string &key) {
    return values[key];
}

// Tests specify the contract.
TEST_CASE("lookup_does_not_insert_and_preserves_stored_zero") {
    std::map<std::string, int> values{{"answer", 42}, {"zero", 0}};
    REQUIRE(read_or_zero(values, "answer") == 42);
    REQUIRE(read_or_zero(values, "zero") == 0);
    REQUIRE(read_or_zero(values, "missing") == 0);
    REQUIRE(values.size() == 2);
    REQUIRE_FALSE(values.contains("missing"));
}
