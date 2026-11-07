// Deterministic hashing for sim state (SIM-04). Never std::hash, never a pointer
// value: the same world must hash identically on every machine and run.
#pragma once

#include <cstddef>
#include <cstdint>

namespace fct {

inline constexpr std::uint64_t kHashSeed = 0x243F6A8885A308D3ull;

// SplitMix64 finaliser: cheap, well-distributed, integer-only.
inline constexpr std::uint64_t hash_mix(std::uint64_t value) {
    value ^= value >> 30;
    value *= 0xBF58476D1CE4E5B9ull;
    value ^= value >> 27;
    value *= 0x94D049BB133111EBull;
    value ^= value >> 31;
    return value;
}

inline constexpr std::uint64_t hash_combine(std::uint64_t seed, std::uint64_t value) {
    return hash_mix(seed ^ (value + 0x9E3779B97F4A7C15ull + (seed << 6) + (seed >> 2)));
}

// FNV-1a over raw bytes: used for asset and save fingerprints, never for state
// that must be reproducible from structure alone.
inline std::uint64_t hash_bytes(const void* data, std::size_t size) {
    const auto* bytes = static_cast<const unsigned char*>(data);
    std::uint64_t hash = 0xCBF29CE484222325ull;
    for (std::size_t i = 0; i < size; ++i) {
        hash ^= static_cast<std::uint64_t>(bytes[i]);
        hash *= 0x100000001B3ull;
    }
    return hash;
}

}  // namespace fct
