// Q16.16 fixed-point arithmetic: the only numeric type allowed inside sim/
// (STYLE-SIM-01). Deterministic across compilers and CPUs because it is pure
// 32/64-bit integer math with defined truncation.
#pragma once

#include <cstdint>

namespace fct {

class Fix {
public:
    static constexpr int kShift = 16;
    static constexpr std::int32_t kOne = static_cast<std::int32_t>(1) << kShift;

    constexpr Fix() = default;

    static constexpr Fix from_raw(std::int32_t raw) {
        Fix value;
        value.raw_ = raw;
        return value;
    }

    // Truncates toward zero; deterministic and documented rather than rounding,
    // because rounding modes are where cross-platform drift comes from.
    static constexpr Fix from_ratio(std::int32_t numerator, std::int32_t denominator) {
        if (denominator == 0) {
            return Fix();
        }
        const std::int64_t scaled =
            (static_cast<std::int64_t>(numerator) << kShift) / denominator;
        return from_raw(static_cast<std::int32_t>(scaled));
    }

    static constexpr Fix from_int(std::int32_t value) {
        return from_raw(value * kOne);
    }

    constexpr std::int32_t raw() const { return raw_; }
    constexpr std::int32_t to_int() const { return raw_ / kOne; }

    constexpr Fix operator+(const Fix& other) const {
        return from_raw(raw_ + other.raw_);
    }
    constexpr Fix operator-(const Fix& other) const {
        return from_raw(raw_ - other.raw_);
    }
    constexpr Fix operator-() const { return from_raw(-raw_); }

    // Division by zero yields zero instead of trapping: sim rules must stay
    // branch-free of UB so a malformed factory cannot crash the tick.
    constexpr Fix div_by(const Fix& other) const {
        if (other.raw_ == 0) {
            return Fix();
        }
        const std::int64_t scaled = (static_cast<std::int64_t>(raw_) << kShift) / other.raw_;
        return from_raw(static_cast<std::int32_t>(scaled));
    }

    constexpr Fix mul_by(const Fix& other) const {
        const std::int64_t product = static_cast<std::int64_t>(raw_) * other.raw_;
        return from_raw(static_cast<std::int32_t>(product >> kShift));
    }

    constexpr bool operator==(const Fix& other) const { return raw_ == other.raw_; }
    constexpr bool operator!=(const Fix& other) const { return raw_ != other.raw_; }
    constexpr bool operator<(const Fix& other) const { return raw_ < other.raw_; }
    constexpr bool operator<=(const Fix& other) const { return raw_ <= other.raw_; }
    constexpr bool operator>(const Fix& other) const { return raw_ > other.raw_; }
    constexpr bool operator>=(const Fix& other) const { return raw_ >= other.raw_; }

private:
    std::int32_t raw_ = 0;
};

}  // namespace fct
