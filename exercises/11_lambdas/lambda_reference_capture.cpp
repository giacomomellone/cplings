// Difficulty: Moderate (2/5)
// Let a callback update a still-live caller-owned value.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"

auto counter_for(int &value) {
  return [value]() mutable { return ++value; };
}

// Tests specify the contract.
TEST_CASE("callback_updates_live_caller_state") {
  int value = 3;
  auto callback = counter_for(value);
  REQUIRE(callback() == 4);
  REQUIRE(value == 4);
  REQUIRE(callback() == 5);
  REQUIRE(value == 5);
}
