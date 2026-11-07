#include <cstdint>

#include "core/fixed.h"
#include "core/hash.h"
#include "core/version.h"
#include "harness.h"

namespace {

using fct::Fix;

}  // namespace

TEST_CASE(fixed_round_trips_integers) {
    CHECK_EQ(Fix::from_int(7).to_int(), 7);
    CHECK_EQ(Fix::from_int(-3).to_int(), -3);
}

TEST_CASE(fixed_addition_is_exact) {
    const Fix sum = Fix::from_int(2) + Fix::from_int(3);
    CHECK_EQ(sum.to_int(), 5);
    CHECK_EQ(sum.raw(), 5 * Fix::kOne);
}

TEST_CASE(fixed_multiplication_truncates_toward_zero) {
    CHECK_EQ(Fix::from_int(3).mul_by(Fix::from_int(4)).to_int(), 12);

    const Fix half = Fix::from_ratio(1, 2);
    CHECK_EQ(half.raw(), Fix::kOne / 2);
    CHECK_EQ(Fix::from_int(5).mul_by(half).to_int(), 2);

    const Fix negative = Fix::from_int(-5).mul_by(half);
    CHECK_EQ(negative.raw(), -(5 * Fix::kOne / 2));
}

TEST_CASE(fixed_division_is_exact_for_representable_values) {
    CHECK_EQ(Fix::from_int(12).div_by(Fix::from_int(4)).to_int(), 3);
    CHECK_EQ(Fix::from_ratio(1, 3).div_by(Fix::from_ratio(1, 3)).to_int(), 1);
}

TEST_CASE(fixed_division_by_zero_is_defined) {
    // Documented behaviour: zero, never a trap. A malformed factory must not be
    // able to crash a tick (SIM rules require no UB in sim/).
    CHECK_EQ(Fix::from_int(1).div_by(Fix()).raw(), 0);
}

TEST_CASE(fixed_comparisons_are_ordered) {
    CHECK(Fix::from_int(1) < Fix::from_int(2));
    CHECK(Fix::from_int(2) <= Fix::from_int(2));
    CHECK(Fix::from_int(3) > Fix::from_int(2));
    CHECK(Fix::from_int(3) >= Fix::from_int(3));
    CHECK(Fix::from_int(3) != Fix::from_int(4));
}

TEST_CASE(hash_is_stable_for_identical_inputs) {
    const std::uint64_t first = fct::hash_combine(fct::kHashSeed, 42);
    const std::uint64_t second = fct::hash_combine(fct::kHashSeed, 42);
    CHECK_EQ(first, second);

    const std::uint64_t other = fct::hash_combine(fct::kHashSeed, 43);
    CHECK(first != other);
}

TEST_CASE(hash_bytes_detects_a_single_changed_byte) {
    const unsigned char a[4] = {1, 2, 3, 4};
    const unsigned char b[4] = {1, 2, 3, 5};
    CHECK(fct::hash_bytes(a, sizeof(a)) != fct::hash_bytes(b, sizeof(b)));
    CHECK_EQ(fct::hash_bytes(a, sizeof(a)), fct::hash_bytes(a, sizeof(a)));
}

TEST_CASE(build_summary_is_populated) {
    CHECK(fct::build_summary() != nullptr);
    CHECK(fct::kVersion[0] != '\0');
}
