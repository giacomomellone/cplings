// Difficulty: Intermediate (3/5)
// Return an owner when the local text must survive its scope.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <string>
#include <string_view>
#include <type_traits>

std::string_view make_label(int value) {
    return std::string("value=") + std::to_string(value);
}

// Tests specify the contract.
static_assert(std::is_same_v<decltype(make_label(1)), std::string>,
              "The returned label must own its text.");
TEST_CASE("returned_text_survives_the_factory") {
    const auto first = make_label(42);
    const auto second = make_label(-3);
    REQUIRE(first == "value=42");
    REQUIRE(second == "value=-3");
}
