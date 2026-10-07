// Difficulty: Hard (4/5)
// Make an increment indivisible instead of splitting load and store.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <atomic>
#include <barrier>
#include <thread>

int two_increments() {
  std::atomic<int> value{0};
  std::barrier both_loaded{2};
  auto worker = [&] {
    [[maybe_unused]] const int snapshot = value.load();
    both_loaded.arrive_and_wait(); // Keep this interleaving harness.
    value.store(snapshot + 1);
  };
  std::thread first(worker), second(worker);
  first.join();
  second.join();
  return value.load();
}

// Tests specify the contract.
TEST_CASE("atomic_read_modify_write_does_not_lose_an_increment") {
  REQUIRE(two_increments() == 2);
}
