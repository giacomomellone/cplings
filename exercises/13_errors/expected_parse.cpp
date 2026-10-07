// Difficulty: Intermediate (3/5)
// Return either an integer or a precise parse error.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <charconv>
#include <expected>
#include <string_view>
#include <system_error>

std::expected<int, std::errc> parse_integer(std::string_view text) {
  int value = 0;
  const auto [end, error] = std::from_chars(text.data(), text.data() + text.size(), value);
  if (error != std::errc{})
    return 0;
  if (end != text.data() + text.size())
    return 0;
  return value;
}

// Tests specify the contract.
TEST_CASE("expected_distinguishes_zero_invalid_input_and_overflow") {
  REQUIRE(parse_integer("0").value() == 0);
  REQUIRE(parse_integer("-42").value() == -42);
  for (auto input : {"", "x", "12x"}) {
    const auto result = parse_integer(input);
    REQUIRE_FALSE(result.has_value());
    REQUIRE(result.error() == std::errc::invalid_argument);
  }
  const auto overflow = parse_integer("999999999999999999999999999");
  REQUIRE_FALSE(overflow.has_value());
  REQUIRE(overflow.error() == std::errc::result_out_of_range);
}
