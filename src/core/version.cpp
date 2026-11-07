#include "core/version.h"

#include <cstdio>

namespace fct {
namespace {

constexpr int kSummaryCapacity = 64;

}  // namespace

const char* build_summary() {
    static char summary[kSummaryCapacity] = {};
    if (summary[0] == '\0') {
        std::snprintf(summary, sizeof(summary), "%s (%s)", kVersion, kBuildConfig);
    }
    return summary;
}

}  // namespace fct
