// Difficulty: Intermediate (3/5)
// Read a worker result only after joining its thread.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <atomic>
#include <latch>
#include <thread>

int compute_in_worker() {
    std::atomic<int> result{0};
    std::latch allow_finish{1};
    std::thread worker([&] {
        allow_finish.wait();
        result.store(42);
    });
    const int observed = result.load();
    allow_finish.count_down();
    worker.join();
    return observed;
}

// Tests specify the contract.
TEST_CASE("joined_worker_result_is_visible_to_caller") {
    REQUIRE(compute_in_worker() == 42);
}
