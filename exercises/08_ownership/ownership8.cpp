// Difficulty: Hard (4/5)
// Explain why const prevents transferring a unique owner.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <utility>

int take(std::unique_ptr<Tracked> owner) {
    return owner->value;
}
int transfer_once() {
    const auto owner = std::make_unique<Tracked>(42);
    return take(std::move(owner));
}

// Tests specify the contract.
TEST_CASE("move_transfers_and_destroys_exactly_once") {
    const int before = Tracked::destroyed;
    REQUIRE(transfer_once() == 42);
    REQUIRE(Tracked::live == 0);
    REQUIRE(Tracked::destroyed == before + 1);
}
