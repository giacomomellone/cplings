// Difficulty: Easy (1/5)
// Mutate the caller through a reference instead of a copy.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"

int increment(int value) {
  return ++value;
}

// Tests specify the contract.
TEST_CASE("increment_changes_the_caller_but_not_an_independent_copy") {
  int value = 10;
  int copy = value;
  REQUIRE(increment(value) == 11);
  REQUIRE(value == 11);
  REQUIRE(copy == 10);
  REQUIRE(increment(value) == 12);
}
