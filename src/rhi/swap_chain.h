// The swap chain contract. A backend owns a presentable surface; everything above
// rhi/ sees only this interface, so render code compiles against the headless
// backend and the GL backend without knowing which one it was handed (MOD-03).
#pragma once

#include <cstdint>

#include "rhi/command_buffer.h"

namespace fct::rhi {

// Presentable formats the engine ships with. BGRA8 is the window default: it is
// the one 8-bit format every desktop driver offers without a swizzle.
enum class Format : std::uint8_t {
    kBgra8Unorm = 0,
    kRgba8Unorm,
    kRgba16Float,
};

enum class PresentMode : std::uint8_t {
    kFifo = 0,  // vsync; always available
    kMailbox,   // tear-free, lowest latency; falls back to kFifo
};

struct ClearColor {
    float r = 0.0f;
    float g = 0.0f;
    float b = 0.0f;
    float a = 1.0f;
};

struct SwapChainDesc {
    int width_px = 1280;
    int height_px = 720;
    Format format = Format::kBgra8Unorm;
    PresentMode present_mode = PresentMode::kFifo;
    const char* debug_name = "main";
};

// GL 4.6 promises at least 16384 texels per dimension. Rejecting larger sizes
// here keeps a bad resize from ever reaching the driver (ERR-02: validate input
// instead of asserting on it).
inline constexpr int kMaxSwapChainPx = 16384;

inline constexpr bool is_valid_swap_chain_size(int width_px, int height_px) {
    return width_px > 0 && height_px > 0 && width_px <= kMaxSwapChainPx &&
           height_px <= kMaxSwapChainPx;
}

inline constexpr bool is_valid(const SwapChainDesc& desc) {
    return is_valid_swap_chain_size(desc.width_px, desc.height_px);
}

class SwapChain {
public:
    SwapChain() = default;
    virtual ~SwapChain() = default;
    SwapChain(const SwapChain&) = delete;
    SwapChain& operator=(const SwapChain&) = delete;
    SwapChain(SwapChain&&) = delete;
    SwapChain& operator=(SwapChain&&) = delete;

    virtual int width_px() const = 0;
    virtual int height_px() const = 0;
    virtual Format format() const = 0;

    // False when the size is outside [1, kMaxSwapChainPx]; the surface keeps its
    // previous size. A resize never loses an already presented frame.
    virtual bool try_resize(int width_px, int height_px) = 0;

    // Clears the whole back buffer. Cheap on the headless backend, one glClear on
    // the GL one; the loop does not branch on the difference.
    virtual void clear(const ClearColor& color) = 0;

    // False when the surface is lost (device removed, window destroyed). The
    // caller recreates the chain; this one stays valid but presents nothing.
    virtual bool try_present() = 0;

    // Hands the frame's commands to the backend. The headless chain accounts for
    // them (counts, digest); the GL chain will upload and draw. False when the
    // surface is lost or the buffer is rejected.
    virtual bool try_submit(const CommandBuffer& commands) = 0;

    virtual std::uint64_t frames_presented() const = 0;
    virtual std::uint64_t clears_issued() const = 0;
    virtual std::uint64_t submitted_buffers() const = 0;
    virtual std::uint64_t vertices_submitted() const = 0;

    // Digest of every clear and present issued so far. Two runs of the same
    // sequence produce the same value, which is what the loop tests assert on --
    // a present that silently stops happening cannot hide behind a frame count.
    virtual std::uint64_t frame_digest() const = 0;
};

}  // namespace fct::rhi
