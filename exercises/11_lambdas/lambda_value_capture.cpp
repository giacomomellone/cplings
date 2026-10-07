// Difficulty: Moderate (2/5)
// Capture a snapshot instead of observing later mutations.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"

auto snapshot_of(int &value) {
  return [&value] { return value; };
}

// Tests specify the contract.
TEST_CASE("callback_keeps_original_value") {
  int value = 10;
  auto callback = snapshot_of(value);
  value = 20;
  REQUIRE(callback() == 10);
  REQUIRE(value == 20);
}
