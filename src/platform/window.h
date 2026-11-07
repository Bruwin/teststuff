// Window and input, behind SDL3 -- or a headless stub when the build has no
// SDL3. No SDL type appears above this header (MOD-03): the native handle is an
// opaque void* and only the backend casts it.
//
// The stub is not a test double bolted on: continuous integration runs on
// machines without a GPU, so "no window" is a supported configuration and the
// app has to stay green there (verify.sh).
#pragma once

#include <cstddef>
#include <cstdint>

namespace fct::platform {

enum class Key : std::uint8_t {
    kUnknown = 0,
    kEscape,
    kW,
    kA,
    kS,
    kD,
    kSpace,
    kShift,
    kCount,
};

inline constexpr std::size_t kKeyCount = static_cast<std::size_t>(Key::kCount);

struct InputSnapshot {
    bool pressed[kKeyCount] = {};
    float mouse_x = 0.0f;
    float mouse_y = 0.0f;
    bool quit = false;
};

inline bool is_pressed(const InputSnapshot& input, Key key) {
    const std::size_t index = static_cast<std::size_t>(key);
    return index < kKeyCount && input.pressed[index];
}

struct WindowDesc {
    const char* title = "factory";
    int width = 1280;
    int height = 720;
    bool resizable = true;
};

class Window {
public:
    Window() = default;
    ~Window();
    Window(const Window&) = delete;
    Window& operator=(const Window&) = delete;

    // False only when a real window was requested and could not be created.
    bool open(const WindowDesc& desc);
    void close();
    bool is_open() const;
    bool is_headless() const { return headless_; }

    // Drains platform events into the snapshot. Called once per frame.
    void poll(InputSnapshot& input);

    // Presents the back buffer. A no-op until the renderer lands (M3):
    // call sites already exist so M3 does not change the loop shape.
    void present();

    int width() const { return width_; }
    int height() const { return height_; }

private:
    void* handle_ = nullptr;  // SDL_Window* in the SDL backend, null in the stub
    bool open_ = false;
    bool headless_ = true;
    int width_ = 0;
    int height_ = 0;
};

}  // namespace fct::platform
