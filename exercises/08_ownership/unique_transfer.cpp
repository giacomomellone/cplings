// Difficulty: Moderate (2/5)
// Transfer a unique owner explicitly and observe its empty source.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <utility>

int consume(std::unique_ptr<int> owner) {
    return *owner;
}
int transfer(std::unique_ptr<int> &owner) {
    return consume(owner);
}

// Tests specify the contract.
TEST_CASE("consuming_owner_empties_the_source") {
    auto owner = std::make_unique<int>(42);
    REQUIRE(transfer(owner) == 42);
    REQUIRE(owner == nullptr);
}
