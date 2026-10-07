// Difficulty: Hard (4/5)
// Break a shared ownership cycle with a non-owning back-link.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"

struct Node {
  static inline int live = 0;
  std::shared_ptr<Node> next;
  std::shared_ptr<Node> previous;
  Node() {
    ++live;
  }
  ~Node() {
    --live;
  }
};
std::weak_ptr<Node> make_pair() {
  auto first = std::make_shared<Node>();
  auto second = std::make_shared<Node>();
  first->next = second;
  second->previous = first;
  return second;
}

// Tests specify the contract.
TEST_CASE("observer_does_not_keep_a_cycle_alive") {
  const auto observer = make_pair();
  REQUIRE(observer.expired());
  REQUIRE(Node::live == 0);
}
