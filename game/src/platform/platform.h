// Platform layer entry point (PLAN.md section 3). Everything the rest of the
// engine may use from this module is reachable from here; the SDL backend and
// the headless stub are interchangeable implementations.
#pragma once

#include "platform/time.h"
#include "platform/window.h"
