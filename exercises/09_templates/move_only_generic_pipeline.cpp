// Difficulty: Difficult (5/5)
// Compose a constrained callable, unique ownership, and an error result.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <concepts>
#include <expected>
#include <functional>
#include <string>
#include <utility>

using Result = std::expected<std::unique_ptr<Tracked>, std::string>;
template <class F>
    requires std::invocable<F &, std::unique_ptr<Tracked>> &&
             std::same_as<std::invoke_result_t<F &, std::unique_ptr<Tracked>>, Result>
Result pipeline(std::unique_ptr<Tracked> input, F &&transform) {
    if (!input)
        return std::unexpected("missing input");
    return std::invoke(transform, input);
}

// Tests specify the contract.
TEST_CASE("pipeline_preserves_one_owner_and_supports_a_move_only_callable") {
    const int before = Tracked::destroyed;
    {
        auto transform = [bias =
                              std::make_unique<int>(5)](std::unique_ptr<Tracked> value) -> Result {
            value->value += *bias;
            return value;
        };
        auto input = std::make_unique<Tracked>(7);
        auto result = pipeline(std::move(input), std::move(transform));
        REQUIRE(input == nullptr);
        REQUIRE(result.has_value());
        REQUIRE((*result)->value == 12);
        REQUIRE(Tracked::live == 1);
    }
    REQUIRE(Tracked::live == 0);
    REQUIRE(Tracked::destroyed == before + 1);
}
TEST_CASE("pipeline_error_releases_input_and_empty_input_skips_the_stage") {
    const int before = Tracked::destroyed;
    bool called = false;
    auto reject = [&](std::unique_ptr<Tracked>) -> Result {
        called = true;
        return std::unexpected("rejected");
    };
    const auto rejected = pipeline(std::make_unique<Tracked>(7), reject);
    REQUIRE_FALSE(rejected.has_value());
    REQUIRE(rejected.error() == "rejected");
    REQUIRE(called);
    REQUIRE(Tracked::live == 0);
    REQUIRE(Tracked::destroyed == before + 1);
    called = false;
    const auto missing = pipeline(nullptr, reject);
    REQUIRE_FALSE(missing.has_value());
    REQUIRE(missing.error() == "missing input");
    REQUIRE_FALSE(called);
}
