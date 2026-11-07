#include "core/log.h"

#include <cstdio>
#include <cstdlib>

namespace fct {
namespace {

constexpr std::size_t kMessageCapacity = 512;

LogLevel g_level = LogLevel::kInfo;
LogSink g_sink = nullptr;

char level_tag(LogLevel level) {
    switch (level) {
        case LogLevel::kDebug:
            return 'D';
        case LogLevel::kInfo:
            return 'I';
        case LogLevel::kWarn:
            return 'W';
        case LogLevel::kError:
            return 'E';
    }
    return '?';
}

void emit(LogLevel level, const char* file, int line, const char* format, std::va_list args) {
    if (static_cast<int>(level) < static_cast<int>(g_level)) {
        return;
    }
    char buffer[kMessageCapacity];
    std::vsnprintf(buffer, sizeof(buffer), format, args);
    if (g_sink != nullptr) {
        g_sink(level, file, line, buffer);
        return;
    }
    std::fprintf(stderr, "[%c] %s:%d %s\n", level_tag(level), file, line, buffer);
}

}  // namespace

void log_set_level(LogLevel level) { g_level = level; }

void log_set_sink(LogSink sink) { g_sink = sink; }

void log_message(LogLevel level, const char* file, int line, const char* format, ...) {
    std::va_list args;
    va_start(args, format);
    emit(level, file, line, format, args);
    va_end(args);
}

void assert_failed(const char* expression, const char* file, int line) {
    std::fprintf(stderr, "[E] %s:%d assertion failed: %s\n", file, line, expression);
    std::abort();
}

}  // namespace fct
