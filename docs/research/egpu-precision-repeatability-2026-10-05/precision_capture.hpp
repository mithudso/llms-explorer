#pragma once
#include "ggml-backend.h"
#include "llama.h"
#include <cerrno>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <limits.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

// Diagnostic only. Installing cb_eval changes scheduler synchronization.
// This is not a throughput arm or an acceptance threshold adjustment.
struct llmsx_precision_state {
    int fd = -1;
    unsigned norm_count = 0;
    unsigned output_count = 0;
    size_t bytes_written = 0;
    unsigned layout_count = 0;
    unsigned empty_pairs = 0;
    unsigned sample_count = 0;
    bool empty_norm_pending = false;
    std::vector<float> last_logits;
    static constexpr unsigned max_pairs = 64;
    static constexpr size_t max_bytes = max_pairs * (993280 + 20480 + 8192);
    ~llmsx_precision_state() { if (fd >= 0) close(fd); }
};

static llmsx_precision_state * llmsx_precision_active = nullptr;

static void llmsx_capture_write(int dir, const char * name, const void * bytes, size_t size) {
    const int fd = openat(dir, name, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
    if (fd < 0) GGML_ABORT("precision capture open failed: %s", strerror(errno));
    const char * data = static_cast<const char *>(bytes);
    size_t offset = 0;
    while (offset < size) {
        const ssize_t n = write(fd, data + offset, size - offset);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) GGML_ABORT("precision capture write failed");
        offset += static_cast<size_t>(n);
    }
    if (close(fd) != 0) GGML_ABORT("precision capture close failed");
}

static bool llmsx_precision_capture(ggml_tensor * tensor, bool ask, void * data) {
    auto * state = static_cast<llmsx_precision_state *>(data);
    const bool norm = strcmp(tensor->name, "result_norm") == 0;
    const bool output = strcmp(tensor->name, "result_output") == 0;
    if (ask) return norm || output;
    if (!norm && !output) return true;
    const int64_t elements = norm ? 5120 : 248320;
    if (state->layout_count >= state->max_pairs * 4) GGML_ABORT("precision layout event bound exceeded");
    char layout[1024], layout_name[128];
    const int layout_length = snprintf(layout, sizeof(layout),
        "{\"version\":\"1.0.1\",\"event\":%u,\"tensor\":\"%s\",\"type_id\":%d,\"shape\":[%lld,%lld,%lld,%lld],\"strides\":[%zu,%zu,%zu,%zu],\"nbytes\":%zu,\"op\":\"%s\"}\n",
        state->layout_count, tensor->name, static_cast<int>(tensor->type),
        (long long) tensor->ne[0], (long long) tensor->ne[1], (long long) tensor->ne[2], (long long) tensor->ne[3],
        tensor->nb[0], tensor->nb[1], tensor->nb[2], tensor->nb[3], ggml_nbytes(tensor), ggml_op_name(tensor->op));
    if (layout_length <= 0 || (size_t) layout_length >= sizeof(layout)) GGML_ABORT("precision layout metadata overflow");
    snprintf(layout_name, sizeof(layout_name), "layout-%04u.json", state->layout_count++);
    llmsx_capture_write(state->fd, layout_name, layout, (size_t) layout_length);
    state->bytes_written += (size_t) layout_length;
    if (tensor->type != GGML_TYPE_F32 || tensor->ne[0] != elements ||
        (tensor->ne[1] != 0 && tensor->ne[1] != 1) || tensor->ne[2] != 1 || tensor->ne[3] != 1 ||
        tensor->nb[0] != sizeof(float)) GGML_ABORT("precision capture unsupported tensor layout; see layout receipt");
    if (tensor->ne[1] == 0) {
        if (ggml_nbytes(tensor) != 0 || state->empty_pairs >= state->max_pairs ||
            state->norm_count != state->output_count ||
            (norm && state->empty_norm_pending) || (output && !state->empty_norm_pending))
            GGML_ABORT("precision empty-output pairing or size violated");
        state->empty_norm_pending = norm;
        if (output) ++state->empty_pairs;
        if (state->bytes_written > state->max_bytes) GGML_ABORT("precision capture aggregate output bound violated");
        return true; // Checkpoint-prefill with no requested output. No tensor read or valid pair increment.
    }
    if (state->empty_norm_pending || !ggml_is_contiguous(tensor) ||
        ggml_nbytes(tensor) != (size_t) elements * sizeof(float))
        GGML_ABORT("precision nonempty tensor layout or pair violated");
    unsigned & count = norm ? state->norm_count : state->output_count;
    if (count >= state->max_pairs ||
        (norm && state->norm_count != state->output_count) ||
        (output && state->norm_count != state->output_count + 1)) {
        GGML_ABORT("precision capture count or pair order violated");
    }
    const size_t size = static_cast<size_t>(elements) * sizeof(float);
    std::vector<float> values(static_cast<size_t>(elements));
    // The scheduler synchronizes this tensor's backend before cb_eval(false).
    ggml_backend_tensor_get(tensor, values.data(), 0, size);
    for (float value : values) if (!std::isfinite(value)) GGML_ABORT("precision capture nonfinite tensor");
    char name[128];
    snprintf(name, sizeof(name), "%04u-%s.f32", count, norm ? "result_norm" : "result_output");
    llmsx_capture_write(state->fd, name, values.data(), size);
    char metadata[1024];
    const int length = snprintf(metadata, sizeof(metadata),
        "{\"version\":\"1.0.0\",\"pair\":%u,\"tensor\":\"%s\",\"dtype\":\"F32\",\"shape\":[%lld,1,1,1],\"bytes\":%zu,\"op\":\"%s\",\"pre_sampler\":true,\"finite\":true,\"contiguous\":true}\n",
        count, tensor->name, static_cast<long long>(elements), size, ggml_op_name(tensor->op));
    if (length <= 0 || static_cast<size_t>(length) >= sizeof(metadata)) GGML_ABORT("precision capture metadata overflow");
    snprintf(name, sizeof(name), "%04u-%s.json", count, norm ? "result_norm" : "result_output");
    llmsx_capture_write(state->fd, name, metadata, static_cast<size_t>(length));
    state->bytes_written += size + static_cast<size_t>(length);
    if (state->bytes_written > state->max_bytes) GGML_ABORT("precision capture aggregate output bound violated");
    if (output) state->last_logits = std::move(values);
    ++count;
    return true;
}

static llmsx_precision_state * llmsx_precision_init() {
    const char * path = getenv("LLMSX_PRECISION_CAPTURE_DIR");
    if (!path) return nullptr;
    char resolved[PATH_MAX];
    if (path[0] != '/' || !realpath(path, resolved) || strcmp(path, resolved) != 0)
        GGML_ABORT("precision capture canonical absolute directory required");
    static llmsx_precision_state state;
    if (state.fd >= 0) GGML_ABORT("precision capture initialized twice");
    state.fd = open(path, O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    struct stat info;
    if (state.fd < 0 || fstat(state.fd, &info) != 0 || !S_ISDIR(info.st_mode) ||
        info.st_uid != getuid() || (info.st_mode & 077) != 0)
        GGML_ABORT("precision capture owned private directory required");
    llmsx_precision_active = &state;
    return &state;
}

static void llmsx_precision_validate_sample(llama_context * ctx, int token_index) {
    auto * state = llmsx_precision_active;
    if (!state) return;
    if (state->sample_count >= state->max_pairs || state->empty_norm_pending ||
        state->norm_count != state->output_count || state->last_logits.size() != 248320)
        GGML_ABORT("precision sample capture state violated");
    const float * actual = llama_get_logits_ith(ctx, token_index);
    const float * base = llama_get_logits(ctx);
    if (!actual || !base || actual != base ||
        memcmp(actual, state->last_logits.data(), 993280) != 0)
        GGML_ABORT("precision capture does not match exact sampled output row");
    char metadata[1024], name[128];
    const int length = snprintf(metadata, sizeof(metadata),
        "{\"version\":\"1.0.1\",\"sample\":%u,\"pair\":%u,\"batch_token_index\":%d,\"output_row\":0,\"raw_logits_bitwise_match\":true,\"pre_sampler\":true}\n",
        state->sample_count, state->output_count - 1, token_index);
    if (length <= 0 || (size_t) length >= sizeof(metadata)) GGML_ABORT("precision sample metadata overflow");
    snprintf(name, sizeof(name), "sample-%04u.json", state->sample_count++);
    llmsx_capture_write(state->fd, name, metadata, (size_t) length);
    state->bytes_written += (size_t) length;
    if (state->bytes_written > state->max_bytes) GGML_ABORT("precision capture aggregate output bound violated");
}
