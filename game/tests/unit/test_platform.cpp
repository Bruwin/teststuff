#include "core/log.h"
#include "harness.h"
#include "platform/platform.h"

namespace {

void discard(fct::LogLevel, const char*, int, const char*) {}

void silence() { fct::log_set_sink(&discard); }

}  // namespace

TEST_CASE(platform_monotonic_clock_never_goes_backwards) {
    const std::int64_t first = fct::platform::monotonic_ns();
    const std::int64_t second = fct::platform::monotonic_ns();
    CHECK(second >= first);
    CHECK(first > 0);
}

TEST_CASE(platform_sleep_with_zero_or_negative_duration_returns_immediately) {
    fct::platform::sleep_for_ns(0);
    fct::platform::sleep_for_ns(-1);
    CHECK(true);
}

TEST_CASE(platform_window_opens_and_reports_its_mode) {
    silence();
    fct::platform::Window window;
    fct::platform::WindowDesc desc;
    desc.width = 640;
    desc.height = 480;

    CHECK(window.open(desc));
    CHECK(window.is_open());
    CHECK_EQ(window.width(), 640);
    CHECK_EQ(window.height(), 480);

    window.close();
    CHECK(!window.is_open());
}

TEST_CASE(platform_input_snapshot_defaults_to_nothing_pressed) {
    silence();
    fct::platform::Window window;
    fct::platform::InputSnapshot input{};
    window.poll(input);

    CHECK(!input.quit);
    CHECK(!fct::platform::is_pressed(input, fct::platform::Key::kEscape));
    CHECK(!fct::platform::is_pressed(input, fct::platform::Key::kW));
    CHECK_EQ(input.mouse_x, 0.0f);
    CHECK_EQ(input.mouse_y, 0.0f);
}

TEST_CASE(platform_headless_window_accepts_frames) {
    // verify.sh and CI run without a display: present() must be a safe no-op and
    // the loop must still terminate on request.
    silence();
    fct::platform::Window window;
    fct::platform::WindowDesc desc;
    CHECK(window.open(desc));

    fct::platform::InputSnapshot input{};
    for (int frame = 0; frame < 3; ++frame) {
        window.poll(input);
        window.present();
    }
    CHECK(window.is_open());
}
