// Difficulty: Hard (4/5)
// Keep the previous value unchanged when validation throws.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <stdexcept>
#include <string>
#include <utility>

void rename(std::string& current, std::string candidate) {
    current.clear();
    if (candidate.empty()) throw std::invalid_argument("empty name");
    current = std::move(candidate);
}

// Tests specify the contract.
TEST_CASE("failed_update_preserves_previous_state") {
    std::string name = "Ada";
    REQUIRE_THROWS_AS(rename(name, ""), std::invalid_argument);
    REQUIRE(name == "Ada");
    rename(name, "Grace");
    REQUIRE(name == "Grace");
}
