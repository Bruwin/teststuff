#include "rhi/gl/gl_loader.h"

#include <cstddef>

namespace fct::rhi::gl {
namespace {

// One line per entry point, in the order the struct declares them. A typo in a
// name here is a null pointer at load time, which try_load_api reports instead of
// letting the device crash later.
template <typename Fn>
void bind(const GlProcLoader& loader, Fn& slot, const char* name) {
    slot = reinterpret_cast<Fn>(loader.load(loader.user, name));
}

}  // namespace

bool try_load_api(const GlProcLoader& loader, fct::gl::GlApi& out) {
    if (loader.load == nullptr) {
        return false;
    }

    bind(loader, out.viewport, "glViewport");
    bind(loader, out.clear_color, "glClearColor");
    bind(loader, out.clear, "glClear");
    bind(loader, out.enable, "glEnable");
    bind(loader, out.disable, "glDisable");
    bind(loader, out.line_width, "glLineWidth");

    bind(loader, out.gen_buffers, "glGenBuffers");
    bind(loader, out.bind_buffer, "glBindBuffer");
    bind(loader, out.buffer_data, "glBufferData");
    bind(loader, out.destroy_buffers, "glDeleteBuffers");

    bind(loader, out.gen_vertex_arrays, "glGenVertexArrays");
    bind(loader, out.bind_vertex_array, "glBindVertexArray");
    bind(loader, out.destroy_vertex_arrays, "glDeleteVertexArrays");

    bind(loader, out.create_shader, "glCreateShader");
    bind(loader, out.shader_source, "glShaderSource");
    bind(loader, out.compile_shader, "glCompileShader");
    bind(loader, out.get_shader_iv, "glGetShaderiv");
    bind(loader, out.destroy_shader, "glDeleteShader");

    bind(loader, out.create_program, "glCreateProgram");
    bind(loader, out.attach_shader, "glAttachShader");
    bind(loader, out.link_program, "glLinkProgram");
    bind(loader, out.get_program_iv, "glGetProgramiv");
    bind(loader, out.use_program, "glUseProgram");

    bind(loader, out.vertex_attrib_pointer, "glVertexAttribPointer");
    bind(loader, out.enable_vertex_attrib_array, "glEnableVertexAttribArray");
    bind(loader, out.draw_arrays, "glDrawArrays");

    bind(loader, out.read_pixels, "glReadPixels");
    bind(loader, out.get_string, "glGetString");
    bind(loader, out.flush, "glFlush");

    return out.is_complete();
}

}  // namespace fct::rhi::gl
