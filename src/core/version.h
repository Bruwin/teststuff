// Build identity. Every log line, save header and net handshake carries this, so
// a bug report can name an exact commit without guesswork.
#pragma once

namespace fct {

inline constexpr const char* kVersion = "0.1.1-m1";

#if defined(NDEBUG)
inline constexpr const char* kBuildConfig = "release";
#else
inline constexpr const char* kBuildConfig = "debug";
#endif

// "<version> (<config>)" in a static buffer; valid for the process lifetime.
const char* build_summary();

}  // namespace fct
