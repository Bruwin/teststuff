// SDL3 backend. Compiled only when CMake finds SDL3 (see CMakeLists.txt); all
// SDL types stay inside this translation unit (MOD-03).
//
// NOTE: this file is exercised by CI (linux/windows jobs install SDL3 when the
// distribution packages it) and by any desktop build. It cannot be compiled in a
// sandbox without SDL3, so treat breakage here as expected first-run work rather
// than as a surprise.
#include "platform/window.h"

#include <SDL3/SDL.h>

#include "core/log.h"

namespace fct::platform {
namespace {

SDL_Window* as_window(void* handle) { return static_cast<SDL_Window*>(handle); }

struct KeyBinding {
    Key key;
    SDL_Scancode scancode;
};

constexpr KeyBinding kBindings[] = {
    {Key::kEscape, SDL_SCANCODE_ESCAPE},
    {Key::kW, SDL_SCANCODE_W},
    {Key::kA, SDL_SCANCODE_A},
    {Key::kS, SDL_SCANCODE_S},
    {Key::kD, SDL_SCANCODE_D},
    {Key::kSpace, SDL_SCANCODE_SPACE},
    {Key::kShift, SDL_SCANCODE_LSHIFT},
};

}  // namespace

Window::~Window() { close(); }

bool Window::open(const WindowDesc& desc) {
    if (handle_ != nullptr) {
        return true;  // already open
    }
    if (!SDL_Init(SDL_INIT_VIDEO)) {
        FCT_LOG_ERROR("SDL_Init(VIDEO) failed: %s", SDL_GetError());
        return false;
    }

    const SDL_WindowFlags flags = desc.resizable ? SDL_WINDOW_RESIZABLE : 0;
    SDL_Window* window = SDL_CreateWindow(desc.title, desc.width, desc.height, flags);
    if (window == nullptr) {
        FCT_LOG_ERROR("SDL_CreateWindow failed: %s", SDL_GetError());
        SDL_Quit();
        return false;
    }

    handle_ = window;
    open_ = true;
    headless_ = false;
    SDL_GetWindowSize(window, &width_, &height_);
    FCT_LOG_INFO("platform: SDL3 window %dx%d", width_, height_);
    return true;
}

void Window::close() {
    if (handle_ != nullptr) {
        SDL_DestroyWindow(as_window(handle_));
        handle_ = nullptr;
        SDL_Quit();
    }
    open_ = false;
    headless_ = true;
    width_ = 0;
    height_ = 0;
}

bool Window::is_open() const { return open_; }

void Window::poll(InputSnapshot& input) {
    input.quit = false;
    SDL_Event event{};
    while (SDL_PollEvent(&event)) {
        if (event.type == SDL_EVENT_QUIT ||
            event.type == SDL_EVENT_WINDOW_CLOSE_REQUESTED) {
            input.quit = true;
        }
    }
    if (handle_ == nullptr) {
        return;
    }

    int key_count = 0;
    const bool* keys = SDL_GetKeyboardState(&key_count);
    for (const KeyBinding& binding : kBindings) {
        const int index = static_cast<int>(binding.scancode);
        input.pressed[static_cast<std::size_t>(binding.key)] =
            keys != nullptr && index < key_count && keys[index];
    }

    float mouse_x = 0.0f;
    float mouse_y = 0.0f;
    SDL_GetMouseState(&mouse_x, &mouse_y);
    input.mouse_x = mouse_x;
    input.mouse_y = mouse_y;

    SDL_GetWindowSize(as_window(handle_), &width_, &height_);
}

void Window::present() {
    // No swap chain until M3; SDL windows on all supported platforms show the
    // last presented framebuffer, which is an empty window for now.
}

}  // namespace fct::platform
