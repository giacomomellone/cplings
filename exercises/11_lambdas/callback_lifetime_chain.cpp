// Difficulty: Difficult (5/5)
// Make every dependency of an escaping callback outlive its creator.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <string>
#include <string_view>
#include <utility>

auto make_callback() {
    std::string prefix(64, 'R');
    auto reading = std::make_unique<Tracked>(7);
    return [prefix = std::string_view(prefix), reading = std::move(reading)] {
        return std::string(prefix) + std::to_string(reading->value);
    };
}

// Tests specify the contract.
TEST_CASE("deferred_callback_owns_text_and_move_only_state") {
    const int before = Tracked::destroyed;
    {
        auto callback = make_callback();
        auto moved = std::move(callback);
        REQUIRE(Tracked::live == 1);
        REQUIRE(moved() == std::string(64, 'R') + "7");
        REQUIRE(moved() == std::string(64, 'R') + "7");
    }
    REQUIRE(Tracked::live == 0);
    REQUIRE(Tracked::destroyed == before + 1);
}
