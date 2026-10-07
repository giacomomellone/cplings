// Difficulty: Easy (1/5)
#include <iostream>

// if1.cpp
// Make me compile! Go to the folder hint if you want a hint :)

// We sometimes encourage you to keep trying things on a given exercise,
// even after you already figured it out.

int bigger(int a, int b) {
  // Complete this function to return the bigger number!
  // Do not use:
  // - another function call
  // - additional variables
}

#include <catch2/catch_test_macros.hpp>

TEST_CASE("ten_is_bigger_than_eight") {
  REQUIRE(bigger(10, 8) == 10);
}

TEST_CASE("fortytwo_is_bigger_than_thirtytwo") {
  REQUIRE(bigger(42, 32) == 42);
}

TEST_CASE("bigger_handles_both_orders_equality_and_negatives") {
  REQUIRE(bigger(8, 10) == 10);
  REQUIRE(bigger(7, 7) == 7);
  REQUIRE(bigger(-9, -2) == -2);
}
