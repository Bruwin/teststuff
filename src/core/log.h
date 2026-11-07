// Logging and assertions. No printf, no iostream: everything goes through here so
// release builds can reroute, rate-limit and capture logs (STYLE-ERR-06).
//
// Output routing: the default sink writes to stderr. A platform or test sink can
// be installed with log_set_sink (file capture, in-game console, test assertions).
#pragma once

#include <cstdarg>

namespace fct {

enum class LogLevel { kDebug, kInfo, kWarn, kError };

// Receives the already-formatted message; must not log recursively.
using LogSink = void (*)(LogLevel level, const char* file, int line, const char* message);

#if defined(__GNUC__) || defined(__clang__)
#define FCT_PRINTF_FORMAT(format_index, first_arg) \
    __attribute__((format(printf, format_index, first_arg)))
#else
#define FCT_PRINTF_FORMAT(format_index, first_arg)
#endif

void log_set_level(LogLevel level);
void log_set_sink(LogSink sink);  // nullptr restores the stderr sink

void log_message(LogLevel level, const char* file, int line, const char* format, ...)
    FCT_PRINTF_FORMAT(4, 5);

// Invariant violation: logs the expression and location, then aborts in every
// configuration. Input validation must use Status instead (ERR-02).
[[noreturn]] void assert_failed(const char* expression, const char* file, int line);

#define FCT_LOG_DEBUG(...) \
    ::fct::log_message(::fct::LogLevel::kDebug, __FILE__, __LINE__, __VA_ARGS__)
#define FCT_LOG_INFO(...) \
    ::fct::log_message(::fct::LogLevel::kInfo, __FILE__, __LINE__, __VA_ARGS__)
#define FCT_LOG_WARN(...) \
    ::fct::log_message(::fct::LogLevel::kWarn, __FILE__, __LINE__, __VA_ARGS__)
#define FCT_LOG_ERROR(...) \
    ::fct::log_message(::fct::LogLevel::kError, __FILE__, __LINE__, __VA_ARGS__)

#define FCT_ASSERT(expression) \
    ((expression) ? static_cast<void>(0) : ::fct::assert_failed(#expression, __FILE__, __LINE__))

}  // namespace fct
