// Difficulty: Intermediate (3/5)
// Release owned resources while a typed exception unwinds the scope.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <stdexcept>

void fail_after_acquiring() {
  [[maybe_unused]] auto *resource = new Tracked{9};
  throw std::runtime_error("reading failed");
}

// Tests specify the contract.
TEST_CASE("unwinding_releases_resource_and_preserves_exception_type") {
  const int before = Tracked::destroyed;
  REQUIRE_THROWS_AS(fail_after_acquiring(), std::runtime_error);
  REQUIRE(Tracked::live == 0);
  REQUIRE(Tracked::destroyed == before + 1);
}
