// Difficulty: Difficult (5/5)
// Make queue waits respond to closure and drain buffered values safely.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <condition_variable>
#include <deque>
#include <future>
#include <latch>
#include <mutex>
#include <optional>
#include <thread>

class Queue {
  std::mutex mutex;
  std::condition_variable changed;
  std::deque<int> values;
  bool closed = false;

public:
  // Supplied test handshakes: signal under the lock, just before waiting.
  std::latch producer_waiting{1};
  std::latch consumer_waiting{1};
  bool push(int value) {
    std::unique_lock lock(mutex);
    if (values.size() == 1 && !closed && !producer_waiting.try_wait())
      producer_waiting.count_down();
    changed.wait(lock, [&] { return values.size() < 1; });
    if (closed)
      return false;
    values.push_back(value);
    changed.notify_all();
    return true;
  }
  std::optional<int> pop() {
    std::unique_lock lock(mutex);
    if (values.empty() && !closed && !consumer_waiting.try_wait())
      consumer_waiting.count_down();
    changed.wait(lock, [&] { return !values.empty(); });
    if (values.empty())
      return std::nullopt;
    const int value = values.front();
    values.pop_front();
    changed.notify_all();
    return value;
  }
  void close() {
    std::lock_guard lock(mutex);
    closed = true;
    changed.notify_all();
  }
};

// Tests specify the contract.
TEST_CASE("queue_handles_notify_before_wait_and_drains_on_close") {
  Queue queue;
  REQUIRE(queue.push(42));
  queue.close();
  REQUIRE(queue.pop().value() == 42);
  REQUIRE_FALSE(queue.pop().has_value());
  REQUIRE_FALSE(queue.push(7));
}
TEST_CASE("closed_empty_queue_returns_immediately") {
  Queue queue;
  queue.close();
  REQUIRE_FALSE(queue.pop().has_value());
}
TEST_CASE("closed_full_queue_rejects_a_waiting_producer") {
  Queue queue;
  REQUIRE(queue.push(1));
  auto producer = std::async(std::launch::async, [&] { return queue.push(2); });
  queue.producer_waiting.wait();
  queue.close();
  REQUIRE_FALSE(producer.get());
  REQUIRE(queue.pop().value() == 1);
  REQUIRE_FALSE(queue.pop().has_value());
}
TEST_CASE("close_wakes_a_waiting_consumer") {
  Queue queue;
  auto consumer = std::async(std::launch::async, [&] { return queue.pop(); });
  queue.consumer_waiting.wait();
  queue.close();
  REQUIRE_FALSE(consumer.get().has_value());
}
TEST_CASE("producer_and_consumer_exchange_without_lost_notifications") {
  Queue queue;
  auto consumer = std::async(std::launch::async, [&] { return queue.pop(); });
  REQUIRE(queue.push(9));
  REQUIRE(consumer.get().value() == 9);
  queue.close();
}
