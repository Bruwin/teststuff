// Minimal test harness. doctest is the intended framework (PLAN.md section 6),
// but M0 must build with zero third-party downloads, so this covers the gap and
// is replaced at M1 when vendoring lands. The macros match doctest's shape so the
// swap is mechanical.
#pragma once

namespace fct::test {

using CaseFn = void (*)();

void register_case(const char* name, CaseFn fn);
int run_all();

bool check(bool condition, const char* expression, const char* file, int line);

template <typename T>
bool check_equal(const T& left, const T& right, const char* expression, const char* file,
                 int line) {
    return check(left == right, expression, file, line);
}

struct Registrar {
    Registrar(const char* name, CaseFn fn) { register_case(name, fn); }
};

}  // namespace fct::test

#define TEST_CASE(name)                                                        \
    static void name();                                                        \
    [[maybe_unused]] static const ::fct::test::Registrar registrar_##name(#name, &name); \
    static void name()

#define CHECK(expression) ::fct::test::check((expression), #expression, __FILE__, __LINE__)

#define CHECK_EQ(left, right)                                                              \
    ::fct::test::check_equal((left), (right), #left " == " #right, __FILE__, __LINE__)
