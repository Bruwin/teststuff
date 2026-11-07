#include <cstring>

#include "core/log.h"
#include "harness.h"

namespace {

int g_calls = 0;
char g_last_message[256] = {};
fct::LogLevel g_last_level = fct::LogLevel::kDebug;

void capture_sink(fct::LogLevel level, const char*, int, const char* message) {
    ++g_calls;
    g_last_level = level;
    std::strncpy(g_last_message, message, sizeof(g_last_message) - 1);
    g_last_message[sizeof(g_last_message) - 1] = '\0';
}

void discard_sink(fct::LogLevel, const char*, int, const char*) {}

}  // namespace

TEST_CASE(log_sink_receives_the_formatted_message) {
    g_calls = 0;
    g_last_message[0] = '\0';
    fct::log_set_level(fct::LogLevel::kDebug);
    fct::log_set_sink(&capture_sink);

    FCT_LOG_INFO("value=%d", 42);

    CHECK_EQ(g_calls, 1);
    CHECK(g_last_level == fct::LogLevel::kInfo);
    CHECK(std::strcmp(g_last_message, "value=42") == 0);
}

TEST_CASE(log_level_filters_below_the_threshold) {
    g_calls = 0;
    fct::log_set_sink(&capture_sink);
    fct::log_set_level(fct::LogLevel::kError);

    FCT_LOG_INFO("dropped");
    CHECK_EQ(g_calls, 0);

    FCT_LOG_ERROR("kept");
    CHECK_EQ(g_calls, 1);
    CHECK(g_last_level == fct::LogLevel::kError);
}

TEST_CASE(log_sink_can_be_restored_to_the_default) {
    fct::log_set_level(fct::LogLevel::kDebug);
    fct::log_set_sink(&capture_sink);
    fct::log_set_sink(nullptr);  // back to stderr

    g_calls = 0;
    FCT_LOG_WARN("this one goes to stderr");
    CHECK_EQ(g_calls, 0);

    fct::log_set_sink(&discard_sink);
}

TEST_CASE(log_keeps_state_between_calls) {
    g_calls = 0;
    fct::log_set_level(fct::LogLevel::kDebug);
    fct::log_set_sink(&capture_sink);

    FCT_LOG_DEBUG("one");
    FCT_LOG_DEBUG("two");

    CHECK_EQ(g_calls, 2);
    CHECK(std::strcmp(g_last_message, "two") == 0);
    fct::log_set_sink(&discard_sink);
    fct::log_set_level(fct::LogLevel::kInfo);
}
