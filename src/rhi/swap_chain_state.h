// Backend-independent swap chain bookkeeping: size validation, clear and present
// counting, and a digest of the frames submitted. Every backend drives this, so
// the loop behaves and reports identically whether or not there is a GPU -- which
// is what lets CI assert on render loop behaviour at all.
#pragma once

#include <cstdint>

#include "core/hash.h"
#include "rhi/swap_chain.h"

namespace fct::rhi {

class SwapChainState {
public:
    explicit SwapChainState(const SwapChainDesc& desc)
        : width_px_(desc.width_px),
          height_px_(desc.height_px),
          format_(desc.format),
          present_mode_(desc.present_mode),
          digest_(initial_digest(desc)) {}

    int width_px() const { return width_px_; }
    int height_px() const { return height_px_; }
    Format format() const { return format_; }
    PresentMode present_mode() const { return present_mode_; }
    std::uint64_t frames_presented() const { return frames_presented_; }
    std::uint64_t clears_issued() const { return clears_issued_; }
    std::uint64_t frame_digest() const { return digest_; }
    bool is_lost() const { return is_lost_; }

    // Same validation as the desc, so a window manager cannot resize us to zero
    // and a bad call leaves the surface untouched.
    bool try_resize(int width_px, int height_px) {
        if (!is_valid_swap_chain_size(width_px, height_px)) {
            return false;
        }
        width_px_ = width_px;
        height_px_ = height_px;
        digest_ = fct::hash_combine(digest_, pack_size(width_px, height_px));
        return true;
    }

    void clear(const ClearColor& color) {
        ++clears_issued_;
        const std::uint64_t quantised = (channel(color.r) << 24) | (channel(color.g) << 16) |
                                        (channel(color.b) << 8) | channel(color.a);
        digest_ = fct::hash_combine(digest_, quantised);
    }

    // A lost surface drops presents rather than counting them: a frame that never
    // reached the screen must not look presented in the stats.
    bool try_present() {
        if (is_lost_) {
            return false;
        }
        ++frames_presented_;
        digest_ = fct::hash_combine(digest_, frames_presented_);
        return true;
    }

    void mark_lost() { is_lost_ = true; }

private:
    static std::uint64_t initial_digest(const SwapChainDesc& desc) {
        std::uint64_t digest =
            fct::hash_combine(fct::kHashSeed, pack_size(desc.width_px, desc.height_px));
        digest = fct::hash_combine(digest, static_cast<std::uint64_t>(desc.format));
        return fct::hash_combine(digest, static_cast<std::uint64_t>(desc.present_mode));
    }

    static std::uint64_t pack_size(int width_px, int height_px) {
        return (static_cast<std::uint64_t>(width_px) << 32) |
               static_cast<std::uint64_t>(height_px);
    }

    // Colours are quantised to 8 bits before hashing: the digest has to survive
    // the difference between two ways of computing the same shade.
    static std::uint64_t channel(float value) {
        const float clamped = value < 0.0f ? 0.0f : (value > 1.0f ? 1.0f : value);
        return static_cast<std::uint64_t>(clamped * 255.0f + 0.5f);
    }

    int width_px_;
    int height_px_;
    Format format_;
    PresentMode present_mode_;
    std::uint64_t frames_presented_ = 0;
    std::uint64_t clears_issued_ = 0;
    std::uint64_t digest_;
    bool is_lost_ = false;
};

}  // namespace fct::rhi
