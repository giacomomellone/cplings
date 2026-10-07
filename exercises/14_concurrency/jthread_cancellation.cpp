// Difficulty: Difficult (5/5)
// Wake a waiting jthread when its stop token is requested.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <atomic>
#include <condition_variable>
#include <mutex>
#include <thread>

bool cancel_waiting_worker() {
  std::mutex mutex;
  std::condition_variable_any changed;
  bool ready = false;
  std::atomic<bool> cancelled{false};
  std::jthread worker([&](std::stop_token stop) {
    std::unique_lock lock(mutex);
    ready = true;
    changed.notify_all();
    changed.wait(lock, [] { return false; });
    cancelled.store(stop.stop_requested());
  });
  {
    std::unique_lock lock(mutex);
    changed.wait(lock, [&] { return ready; });
  }
  worker.request_stop();
  worker.join();
  return cancelled.load();
}

// Tests specify the contract.
TEST_CASE("stop_request_interrupts_a_waiting_worker") {
  REQUIRE(cancel_waiting_worker());
}
