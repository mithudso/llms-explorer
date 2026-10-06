#pragma once
// Host-only diagnostic accounting. This header is included by ggml-cuda.cu only.
#include <atomic>
#include <cstddef>
#include <new>
#if !defined(GGML_CUDA_NO_VMM) || defined(GGML_USE_VMM)
#error "Aggregate diagnostic requires original legacy allocator / NO_VMM contract"
#endif
namespace llmsx_scratch {
constexpr size_t limit = 2147483648ull;
constexpr size_t cublas_per_context = 8ull * 32ull * 1024ull * 1024ull;
static_assert(sizeof(size_t) == 8, "Requires bounded 64-bit host accounting");
static_assert(GGML_CUDA_MAX_STREAMS == 8, "Pinned cuBLAS per-context bound changed");
// One translation-unit ledger, shared by every legacy pool/backend context.
static std::atomic<size_t> reserved {0};
static std::atomic<size_t> peak {0};
static bool reserve(size_t bytes) {
    size_t old = reserved.load();
    for (;;) {
        if (bytes == 0 || old > limit || bytes > limit - old) { return false; }
        if (reserved.compare_exchange_weak(old, old + bytes)) {
            const size_t total = old + bytes;
            size_t high = peak.load();
            while (high < total && !peak.compare_exchange_weak(high, total)) {}
            return true;
        }
    }
}
static void release(size_t bytes) {
    size_t old = reserved.load();
    for (;;) {
        if (bytes == 0 || bytes > old) {
            GGML_ABORT("LLMSX aggregate scratch release refused: reserved=%zu released=%zu", old, bytes);
        }
        if (reserved.compare_exchange_weak(old, old - bytes)) { return; }
    }
}
} // namespace llmsx_scratch
