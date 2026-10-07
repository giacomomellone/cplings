// Difficulty: Difficult (5/5)
// Commit a multi-step update only after all failure points succeed.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <stdexcept>
#include <utility>
#include <vector>

struct Ledger {
  std::vector<int> entries;
  int total;
  bool operator==(const Ledger &) const = default;
};
enum class Failure { none, after_append, after_total };
void post(Ledger &ledger, int amount, Failure fail) {
  ledger.entries.push_back(amount);
  if (amount < 0)
    throw std::invalid_argument("negative amount");
  if (fail == Failure::after_append)
    throw std::runtime_error("append failed");
  ledger.total += amount;
  if (fail == Failure::after_total)
    throw std::runtime_error("total failed");
}

// Tests specify the contract.
TEST_CASE("transaction_has_no_observable_partial_update") {
  const Ledger original{{2, 3}, 5};
  for (auto failure : {Failure::after_append, Failure::after_total}) {
    auto ledger = original;
    REQUIRE_THROWS_AS(post(ledger, 7, failure), std::runtime_error);
    REQUIRE(ledger == original);
  }
  auto ledger = original;
  REQUIRE_THROWS_AS(post(ledger, -1, Failure::none), std::invalid_argument);
  REQUIRE(ledger == original);
  post(ledger, 7, Failure::none);
  REQUIRE(ledger.entries == std::vector<int>{2, 3, 7});
  REQUIRE(ledger.total == 12);
}
