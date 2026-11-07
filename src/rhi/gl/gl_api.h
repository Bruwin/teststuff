// The slice of OpenGL 4.6 this backend uses, declared by hand.
//
// Declaring the types and entry points here instead of including <GL/gl.h> is what
// makes the backend testable: the whole device is written against a table of
// function pointers, so a fake table exercises the real upload and draw sequence
// on a machine with no driver at all. Only the platform is allowed to touch SDL.
#pragma once

#include <cstddef>
#include <cstdint>

namespace fct::gl {

using GLenum = std::uint32_t;
using GLuint = std::uint32_t;
using GLint = std::int32_t;
using GLsizei = std::int32_t;
using GLfloat = float;
using GLchar = char;
using GLbitfield = std::uint32_t;
using GLboolean = std::uint8_t;
using GLubyte = unsigned char;
using GLsizeiptr = std::ptrdiff_t;

inline constexpr GLenum kPoints = 0x0000;
inline constexpr GLenum kLines = 0x0001;
inline constexpr GLenum kTriangles = 0x0004;
inline constexpr GLbitfield kColorBufferBit = 0x00004000;
inline constexpr GLenum kFloat = 0x1406;
inline constexpr GLenum kArrayBuffer = 0x8892;
inline constexpr GLenum kDynamicDraw = 0x88E8;
inline constexpr GLenum kVertexShader = 0x8B31;
inline constexpr GLenum kFragmentShader = 0x8B30;
inline constexpr GLenum kCompileStatus = 0x8B81;
inline constexpr GLenum kLinkStatus = 0x8B82;
inline constexpr GLenum kRgba = 0x1908;
inline constexpr GLenum kUnsignedByte = 0x1401;
inline constexpr GLenum kRenderer = 0x1F01;
inline constexpr GLenum kVersion = 0x1F02;

// Populated by load_api(); every entry must be non-null before a device is made,
// because a partially loaded driver fails at the worst possible moment.
struct GlApi {
    void (*viewport)(GLint x, GLint y, GLsizei width, GLsizei height) = nullptr;
    void (*clear_color)(GLfloat r, GLfloat g, GLfloat b, GLfloat a) = nullptr;
    void (*clear)(GLbitfield mask) = nullptr;
    void (*enable)(GLenum cap) = nullptr;
    void (*disable)(GLenum cap) = nullptr;
    void (*line_width)(GLfloat width) = nullptr;

    void (*gen_buffers)(GLsizei count, GLuint* buffers) = nullptr;
    void (*bind_buffer)(GLenum target, GLuint buffer) = nullptr;
    void (*buffer_data)(GLenum target, GLsizeiptr size, const void* data, GLenum usage) = nullptr;
    void (*destroy_buffers)(GLsizei count, const GLuint* buffers) = nullptr;

    void (*gen_vertex_arrays)(GLsizei count, GLuint* arrays) = nullptr;
    void (*bind_vertex_array)(GLuint array) = nullptr;
    void (*destroy_vertex_arrays)(GLsizei count, const GLuint* arrays) = nullptr;

    GLuint (*create_shader)(GLenum stage) = nullptr;
    void (*shader_source)(GLuint shader, GLsizei count, const GLchar* const* source,
                          const GLint* lengths) = nullptr;
    void (*compile_shader)(GLuint shader) = nullptr;
    void (*get_shader_iv)(GLuint shader, GLenum name, GLint* value) = nullptr;
    void (*destroy_shader)(GLuint shader) = nullptr;

    GLuint (*create_program)() = nullptr;
    void (*attach_shader)(GLuint program, GLuint shader) = nullptr;
    void (*link_program)(GLuint program) = nullptr;
    void (*get_program_iv)(GLuint program, GLenum name, GLint* value) = nullptr;
    void (*use_program)(GLuint program) = nullptr;

    void (*vertex_attrib_pointer)(GLuint index, GLint size, GLenum type, GLboolean normalized,
                                  GLsizei stride, const void* offset) = nullptr;
    void (*enable_vertex_attrib_array)(GLuint index) = nullptr;
    void (*draw_arrays)(GLenum mode, GLint first, GLsizei count) = nullptr;

    void (*read_pixels)(GLint x, GLint y, GLsizei width, GLsizei height, GLenum format,
                        GLenum type, void* pixels) = nullptr;
    const GLubyte* (*get_string)(GLenum name) = nullptr;
    void (*flush)() = nullptr;

    bool is_complete() const {
        return viewport != nullptr && clear_color != nullptr && clear != nullptr &&
               gen_buffers != nullptr && bind_buffer != nullptr && buffer_data != nullptr &&
               destroy_buffers != nullptr && gen_vertex_arrays != nullptr &&
               bind_vertex_array != nullptr && destroy_vertex_arrays != nullptr &&
               create_shader != nullptr && shader_source != nullptr && compile_shader != nullptr &&
               get_shader_iv != nullptr && destroy_shader != nullptr && create_program != nullptr &&
               attach_shader != nullptr && link_program != nullptr &&
               get_program_iv != nullptr && use_program != nullptr &&
               vertex_attrib_pointer != nullptr && enable_vertex_attrib_array != nullptr &&
               draw_arrays != nullptr && read_pixels != nullptr && flush != nullptr;
    }
};

}  // namespace fct::gl
