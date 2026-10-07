// Difficulty: Hard (4/5)
// Constrain a generic operation to non-bool integral types.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <concepts>
#include <string>
#include <type_traits>

template <class T>
  requires true
T doubled(T value) {
  return value + value;
}
template <class T>
concept CanDouble = requires(T value) { doubled(value); };

// Tests specify the contract.
static_assert(CanDouble<int> && CanDouble<long>);
static_assert(!CanDouble<bool>, "bool is not an arithmetic count");
static_assert(!CanDouble<double>, "this interface accepts integers only");
static_assert(!CanDouble<std::string>, "reject strings at the interface");
TEST_CASE("constrained_operation_doubles_signed_values") {
  REQUIRE(doubled(21) == 42);
  REQUIRE(doubled(-3L) == -6L);
}
