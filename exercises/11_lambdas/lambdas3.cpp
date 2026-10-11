// Difficulty: Intermediate (3/5)
// Return a callback that owns a noncopyable resource.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <utility>

auto reader(std::unique_ptr<Tracked> resource) {
    return [resource] { return resource->value; };
}

// Tests specify the contract.
TEST_CASE("returned_closure_owns_resource_until_its_destruction") {
    const int before = Tracked::destroyed;
    {
        auto owner = std::make_unique<Tracked>(42);
        auto callback = reader(std::move(owner));
        REQUIRE(owner == nullptr);
        REQUIRE(Tracked::live == 1);
        REQUIRE(callback() == 42);
        REQUIRE(callback() == 42);
    }
    REQUIRE(Tracked::live == 0);
    REQUIRE(Tracked::destroyed == before + 1);
}
