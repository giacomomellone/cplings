// Difficulty: Moderate (2/5)
// Release a resource on every exit from its scope.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"

int inspect(bool early) {
    auto *resource = new Tracked{7};
    if (early)
        return resource->value;
    const int result = resource->value;
    delete resource;
    return result;
}

// Tests specify the contract.
TEST_CASE("both_return_paths_release_exactly_one_resource") {
    REQUIRE(Tracked::live == 0);
    const int before = Tracked::destroyed;
    REQUIRE(inspect(false) == 7);
    REQUIRE(Tracked::live == 0);
    REQUIRE(inspect(true) == 7);
    REQUIRE(Tracked::live == 0);
    REQUIRE(Tracked::destroyed == before + 2);
}
