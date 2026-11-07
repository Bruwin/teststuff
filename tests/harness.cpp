#include "harness.h"

#include <cstdio>
#include <vector>

namespace fct::test {
namespace {

struct Case {
    const char* name;
    CaseFn fn;
};

std::vector<Case>& cases() {
    static std::vector<Case> storage;
    return storage;
}

int g_failures = 0;

}  // namespace

void register_case(const char* name, CaseFn fn) { cases().push_back(Case{name, fn}); }

bool check(bool condition, const char* expression, const char* file, int line) {
    if (!condition) {
        ++g_failures;
        std::fprintf(stderr, "FAIL %s:%d %s\n", file, line, expression);
    }
    return condition;
}

int run_all() {
    int executed = 0;
    for (const Case& test_case : cases()) {
        const int before = g_failures;
        test_case.fn();
        ++executed;
        if (g_failures != before) {
            std::fprintf(stderr, "  in test: %s\n", test_case.name);
        }
    }
    std::printf("%d test case(s), %d failure(s)\n", executed, g_failures);
    return g_failures == 0 ? 0 : 1;
}

}  // namespace fct::test
