# Session 005 -- M3: first triangle, debug lines, reference rasteriser

**Date:** 2026-11-07
**Milestone:** M3 (triangle and debug lines; hardware backend still pending)
**Outcome:** `verify: OK`, 48 tests, 0 findings.

## The problem M3 actually had

M3 asks for "a textured-free triangle, debug lines, capture screenshot". Two of
those three need a GPU. There is none here -- no SDL3, no GL header, no network --
so the naive reading would be "cannot be done", or worse: several hundred lines of
GL nobody had compiled, reported as done.

The way out is to separate *what* is drawn from *who* draws it:

- `rhi::CommandBuffer` is the description: vertices in clip space, packed RGBA
  colours, bounded capacity, and a digest over the exact bits submitted.
- `render::Rasterizer` is a reference implementation that executes that
  description into an RGBA8 `render::Framebuffer`.
- The GL backend, when it lands, consumes the same `CommandBuffer`. It is a second
  executor, not a second API.

So the triangle is real geometry, drawn by real code, checkable pixel by pixel --
and the same calls reach the device through `SwapChain::try_submit`.

## What shipped

| File | Role |
|---|---|
| `src/rhi/command_buffer.h` | `Vertex`, `Primitive`, `DrawCommand`, `CommandBuffer`, `pack_rgba` |
| `src/render/framebuffer.h` | RGBA8 target: clear, pixel access, coverage, digest |
| `src/render/rasterizer.{h,cpp}` | barycentric triangle fill + DDA lines, clip space to pixels |
| `src/render/render.h` | module API (MOD-06) |
| `tests/unit/test_render.cpp` | 9 cases |
| `src/app/main.cpp` | builds the scene once, submits every frame, logs `covered=` and `frame=` |

The app's scene is a triangle inside a debug box: one fill plus four lines, in the
same command buffer, so a single frame exercises both primitives.

## Decisions worth keeping

1. **Colours are integers.** `pack_rgba` keeps a vertex at 20 bytes and makes the
   command digest exact: no float formatting, no rounding question about whether
   two frames are "the same".
2. **The digest is over bit patterns.** `std::bit_cast<std::uint32_t>` on each
   coordinate means `-0.0f` and `0.0f` are different vertices, and no two distinct
   frames can collide by rounding.
3. **Vertices at or behind the eye are rejected, not clipped.** `w <= 0` returns
   before the divide. Full frustum clipping is a later problem; pretending to do
   it now would add untested branches, so it is stated as absent instead.
4. **No depth buffer.** M3 draws one flat layer. A depth test with one layer is a
   test nothing can fail, so it is deferred to the milestone that has two.
5. **Out-of-range pixels are refused, not clamped.** `try_set_pixel` returns false
   and the rasteriser never scribbles outside the image; a triangle that escapes
   the viewport is a bug worth seeing, not a silent clamp.

## Verified

```
bash tools/verify.sh
  conventions           41 files, 0 findings
  layering              30 files, 0 findings
  gate self-test        4/4 ok
  48 test cases, 0 failures
verify: OK

./build/fct_app --frames 600 -> covered=28138 frame=d5a1...   (stable across runs)
```

Pixel tests, not screenshots: the centre pixel of an 8x8 target carries the
triangle colour, the corner still carries the clear colour, a triangle wholly
outside the viewport changes zero pixels, a degenerate triangle draws nothing, and
a line paints both of its endpoints on the middle row.

## Honest limits

- Nothing has been drawn by hardware. `frame=` is a software rasteriser's output,
  and the GL backend is still the M2b/M3b task that needs a machine with SDL3.
- No clipping against the view frustum, no depth, no textures (by design at M3),
  no anti-aliasing.
- `capture screenshot` from the milestone text is not delivered; `covered=` and
  `frame=` are the headless substitute, and they are what CI can check.

## Next

- M3b: GL backend replays the same `CommandBuffer`; `capture screenshot` becomes a
  readback of the surface.
- M4: scene graph, chunk batcher, a real camera, so the triangle becomes geometry.
