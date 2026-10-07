// Difficulty: Hard (4/5)
// Reacquire an element after vector storage is reallocated.
// Predict the failing result before editing. Fix the learner code, keep the tests.
#include "learning_support.hpp"
#include <vector>

int &first_after_growth(std::vector<int> &values) {
    int &selected = values.front();
    values.reserve(values.capacity() + 1); // Guaranteed reallocation; keep this line.
    return selected;
}

// Tests specify the contract.
TEST_CASE("selected_element_remains_a_live_alias_after_growth") {
    std::vector<int> values{7, 8};
    int &selected = first_after_growth(values);
    REQUIRE(selected == 7);
    selected = 42;
    REQUIRE(values.front() == 42);
    REQUIRE(values[1] == 8);
}
