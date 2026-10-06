/* CPU-only, selected Q5_K output projection control; no backend or model init. */
#define _DARWIN_C_SOURCE
#include <CommonCrypto/CommonDigest.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <unistd.h>
#include "ggml-quants.h"
#include "ggml-cpu/quants.h"

enum { N = 5120, BLOCKS = 20, ROW_BYTES = 3520, SELECTED = 3 };
static const off_t OUTPUT_OFFSET = 10994176;
static const size_t LOGICAL_LIMIT = 32u * 1024u * 1024u;
_Static_assert(sizeof(float) == 4, "Requires F32 ABI");
_Static_assert(sizeof(block_q5_K) == 176, "Requires exact Q5_K ABI");
_Static_assert(sizeof(block_q8_K) == 292, "Requires exact Q8_K ABI");
_Static_assert(N == BLOCKS * QK_K, "Requires 256-value K blocks");
static float norms[2][N];
static float weights[N];
static block_q5_K row[BLOCKS];
static block_q8_K activations[2][BLOCKS];
static float recorded[SELECTED][2];
_Static_assert(sizeof(norms) + sizeof(weights) + sizeof(row) + sizeof(activations) + sizeof(recorded)
               == 76664, "Logical buffer accounting changed");
_Static_assert(sizeof(norms) + sizeof(weights) + sizeof(row) + sizeof(activations) + sizeof(recorded)
               < 32u * 1024u * 1024u, "Selected control exceeds original 32 MiB logical limit");
struct file_binding {
    const char * path;
    long long bytes;
    uint64_t device, inode;
    unsigned uid, mode;
    long long mtime_sec;
    long mtime_nsec;
    long long ctime_sec;
    long ctime_nsec;
};
#include "q5k_row_bindings.h"

static void refuse(const char * why) {
    fprintf(stderr, "CPU row control refused: %s (errno=%d)\n", why, errno);
    exit(1);
}
static bool metadata_matches(const struct stat * s, const struct file_binding * b) {
    return S_ISREG(s->st_mode) && s->st_size == b->bytes && (uint64_t)s->st_dev == b->device &&
        (uint64_t)s->st_ino == b->inode && s->st_uid == b->uid && (s->st_mode & 07777) == b->mode &&
        s->st_mtimespec.tv_sec == b->mtime_sec && s->st_mtimespec.tv_nsec == b->mtime_nsec &&
        s->st_ctimespec.tv_sec == b->ctime_sec && s->st_ctimespec.tv_nsec == b->ctime_nsec;
}
static int open_bound(int index) {
    const struct file_binding * b = &inputs[index];
    char canonical[PATH_MAX];
    struct stat named, opened;
    if (!realpath(b->path, canonical) || strcmp(canonical, b->path) != 0 ||
        lstat(b->path, &named) || !metadata_matches(&named, b)) refuse("canonical input metadata drift");
    int fd = open(b->path, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
    if (fd < 0 || fstat(fd, &opened) || !metadata_matches(&opened, b)) refuse("opened input metadata drift");
    return fd;
}
static void recheck(int fd, int index) {
    const struct file_binding * b = &inputs[index];
    struct stat named, opened;
    char canonical[PATH_MAX];
    if (fstat(fd, &opened) || !metadata_matches(&opened, b) ||
        !realpath(b->path, canonical) || strcmp(canonical, b->path) != 0 ||
        lstat(b->path, &named) || !metadata_matches(&named, b)) refuse("input changed during bounded read");
}
static void read_exact(int fd, int index, off_t offset, void * output, size_t bytes) {
    if (offset < 0 || bytes > LOGICAL_LIMIT || (uint64_t)offset + bytes > (uint64_t)inputs[index].bytes)
        refuse("read bounds");
    size_t done = 0;
    while (done < bytes) {
        ssize_t n = pread(fd, (char *)output + done, bytes-done, offset+(off_t)done);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) refuse("short bounded read");
        done += (size_t)n;
    }
    recheck(fd,index);
}
static void require_hash(const void * data, size_t bytes, const char * expected) {
    unsigned char digest[CC_SHA256_DIGEST_LENGTH];
    char hex[CC_SHA256_DIGEST_LENGTH * 2 + 1];
    if (bytes > LOGICAL_LIMIT || !CC_SHA256(data,(CC_LONG)bytes,digest)) refuse("bounded SHA256 failure");
    for (size_t i=0;i<sizeof(digest);++i) snprintf(hex+2*i,3,"%02x",digest[i]);
    if (strcmp(hex,expected)) refuse("bounded input hash drift");
}
static uint32_t bits(float f) { uint32_t u;memcpy(&u,&f,sizeof(u));return u; }
static double mathematical_dot(const float * a, const float * b) {
    double sum=0,correction=0;
    for (int i=0;i<N;++i) {
        if (!isfinite(a[i]) || !isfinite(b[i])) refuse("nonfinite dequantized weight or norm");
        double adjusted=(double)a[i]*(double)b[i]-correction;
        double updated=sum+adjusted;
        correction=(updated-sum)-adjusted;
        sum=updated;
    }
    return sum;
}
int main(int argc, char ** argv) {
    (void)argv;
    if (argc != 1 || getuid()!=501) refuse("no arguments and UID501 required");
    struct rlimit core={0,0},cpu={30,30};
    if (setrlimit(RLIMIT_CORE,&core) || setrlimit(RLIMIT_CPU,&cpu)) refuse("bounded process limits");
    int fd[5];
    for (int i=0;i<5;++i) fd[i]=open_bound(i);
    for (int j=0;j<2;++j) {
        read_exact(fd[1+j],1+j,0,norms[j],sizeof(norms[j]));
        require_hash(norms[j],sizeof(norms[j]),norm_hashes[j]);
        for (int i=0;i<N;++i) if (!isfinite(norms[j][i])) refuse("nonfinite norm");
        quantize_row_q8_K(norms[j],activations[j],N);
    }
    for (int t=0;t<SELECTED;++t) for(int j=0;j<2;++j) {
        read_exact(fd[3+j],3+j,(off_t)tokens[t]*4,&recorded[t][j],4);
        if (!isfinite(recorded[t][j]) || bits(recorded[t][j])!=expected_logit_bits[t][j])
            refuse("recorded selected logit binding");
    }
    double math_dot[SELECTED][2];
    float cpu_route[SELECTED][2];
    bool oracle_pass=true;
    for (int t=0;t<SELECTED;++t) {
        read_exact(fd[0],0,OUTPUT_OFFSET+(off_t)tokens[t]*ROW_BYTES,row,sizeof(row));
        require_hash(row,sizeof(row),row_hashes[t]);
        dequantize_row_q5_K(row,weights,N);
        for (int j=0;j<2;++j) {
            math_dot[t][j]=mathematical_dot(weights,norms[j]);
            ggml_vec_dot_q5_K_q8_K(N,&cpu_route[t][j],0,row,0,activations[j],0,1);
            if (!isfinite(math_dot[t][j]) || !isfinite(cpu_route[t][j])) refuse("nonfinite dot");
        }
        oracle_pass = oracle_pass && bits(cpu_route[t][0])==bits(recorded[t][0]);
    }
    for (int i=0;i<5;++i) { recheck(fd[i],i);if(close(fd[i]))refuse("input close"); }
    printf("{\n\"scope\":\"selected CPU Q5_K/Q8_K oracle and dequantized-F32 mathematical control\",\n");
    printf("\"logical_buffers_bytes\":%zu,\"logical_limit_bytes\":%zu,\n",
           sizeof(norms)+sizeof(weights)+sizeof(row)+sizeof(activations)+sizeof(recorded),LOGICAL_LIMIT);
    printf("\"model_row_bytes_read\":10560,\"norm_bytes_read\":40960,\"recorded_logit_bytes_read\":24,\n");
    printf("\"GPU_initializations\":0,\"GPU_requests\":0,\"model_inference_requests\":0,\n");
    printf("\"CPU_oracle_all_selected_bitwise\":%s,\"interpret_residuals\":%s,\n\"rows\":[\n",
           oracle_pass?"true":"false",oracle_pass?"true":"false");
    for (int t=0;t<SELECTED;++t) {
        printf("{\"token\":%d,\"recorded_CPU_logit\":%.17g,\"recorded_CUDA_logit\":%.17g,",
               tokens[t],(double)recorded[t][0],(double)recorded[t][1]);
        printf("\"CPU_route_CPU_norm\":%.17g,\"CPU_route_CUDA_norm\":%.17g,\"CPU_oracle_bits_equal\":%s,",
               (double)cpu_route[t][0],(double)cpu_route[t][1],bits(cpu_route[t][0])==bits(recorded[t][0])?"true":"false");
        printf("\"dequantized_F32_dot_CPU_norm_f64\":%.17g,\"dequantized_F32_dot_CUDA_norm_f64\":%.17g,",
               math_dot[t][0],math_dot[t][1]);
        printf("\"shared_CPU_route_hidden_contribution\":%.17g,\"recorded_CUDA_minus_shared_CPU_route_CUDA_norm\":%.17g,",
               (double)cpu_route[t][1]-(double)cpu_route[t][0],(double)recorded[t][1]-(double)cpu_route[t][1]);
        printf("\"shared_mathematical_hidden_contribution\":%.17g,\"recorded_CPU_minus_mathematical_CPU_norm\":%.17g,",
               math_dot[t][1]-math_dot[t][0],(double)recorded[t][0]-math_dot[t][0]);
        printf("\"recorded_CUDA_minus_mathematical_CUDA_norm\":%.17g}%s\n",
               (double)recorded[t][1]-math_dot[t][1],t+1==SELECTED?"":",");
    }
    printf("]\n}\n");
    return oracle_pass ? 0 : 2;
}
