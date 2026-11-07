// Headless backend: built when SDL3 is not available. It satisfies the window
// contract, reports itself as headless, and never produces input. The app turns
// this into a warning rather than a failure, which is what keeps CI and this
// sandbox green without a display.
#include "platform/window.h"

#include "core/log.h"

namespace fct::platform {

Window::~Window() { close(); }

bool Window::open(const WindowDesc& desc) {
    if (handle_ != nullptr) {
        return true;  // already open
    }
    headless_ = true;
    open_ = true;
    width_ = desc.width;
    height_ = desc.height;
    FCT_LOG_INFO("platform: built without SDL3, headless window %dx%d", desc.width, desc.height);
    return true;
}

void Window::close() {
    handle_ = nullptr;
    open_ = false;
    headless_ = true;
    width_ = 0;
    height_ = 0;
}

bool Window::is_open() const { return open_; }

void Window::poll(InputSnapshot& input) { input.quit = false; }

void Window::present() {}

}  // namespace fct::platform
