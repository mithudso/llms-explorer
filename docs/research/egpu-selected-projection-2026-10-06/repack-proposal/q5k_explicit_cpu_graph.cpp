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
#include <typeinfo>
#include "ggml-backend.h"
#include "ggml-cpu.h"
#include "ggml-cpu/repack.h"
#include "ggml-quants.h"
#include "ggml-cpu/quants.h"

enum { N = 5120, BLOCKS = 20, ROW_BYTES = 3520, SELECTED = 3 };
static const off_t OUTPUT_OFFSET = 10994176;
static const size_t LOGICAL_LIMIT = 32u * 1024u * 1024u;
static_assert(sizeof(float) == 4, "Requires F32 ABI");
static_assert(sizeof(block_q5_K) == 176, "Requires exact Q5_K ABI");
static_assert(sizeof(block_q8_K) == 292, "Requires exact Q8_K ABI");
static_assert(N == BLOCKS * QK_K, "Requires 256-value K blocks");
static float norms[2][N];
static float weights[N];
static block_q5_K row[BLOCKS];
static block_q8_K activations[2][BLOCKS];
static float recorded[SELECTED][2];
static_assert(sizeof(norms) + sizeof(weights) + sizeof(row) + sizeof(activations) + sizeof(recorded)
               == 76664, "Logical buffer accounting changed");
static_assert(sizeof(norms) + sizeof(weights) + sizeof(row) + sizeof(activations) + sizeof(recorded)
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
#include "graph_row_bindings.h"

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

// Only eight neighboring output rows are ever resident; no whole-model load.
alignas(64) static unsigned char graph_arena[1048576];
static block_q5_K group[8][BLOCKS];
static constexpr size_t GRAPH_WORK_LIMIT = 1048576;
static_assert(sizeof(graph_arena)+sizeof(group)+sizeof(norms)+sizeof(weights)+sizeof(row)+
              sizeof(activations)+sizeof(recorded)+GRAPH_WORK_LIMIT+65536 < 32u*1024u*1024u,
              "Bounded graph data/workspace exceeds original32MiB logical limit");
int main(int argc, char ** argv) {
    (void)argv;
    if (argc!=1 || getuid()!=501) refuse("no arguments and UID501 required");
    struct rlimit core={0,0},cpu_limit={30,30};
    if(setrlimit(RLIMIT_CORE,&core)||setrlimit(RLIMIT_CPU,&cpu_limit))refuse("bounded process limits");
    int fd[5];for(int i=0;i<5;++i)fd[i]=open_bound(i);
    for(int j=0;j<2;++j){
        read_exact(fd[j+1],j+1,0,norms[j],sizeof(norms[j]));
        require_hash(norms[j],sizeof(norms[j]),norm_hashes[j]);
        for(int k=0;k<N;++k)if(!isfinite(norms[j][k]))refuse("nonfinite norm");
    }
    for(int t=0;t<SELECTED;++t)for(int j=0;j<2;++j){
        read_exact(fd[j+3],j+3,(off_t)tokens[t]*4,&recorded[t][j],4);
        if(!isfinite(recorded[t][j])||bits(recorded[t][j])!=expected_logit_bits[t][j])refuse("selected recorded logit binding");
    }
    // Explicit CPU init only; do not use generic backend loading or discovery.
    ggml_backend_t backend=ggml_backend_cpu_init();
    if(!backend||!ggml_backend_is_cpu(backend))refuse("explicit CPU backend unavailable");
    ggml_backend_cpu_set_n_threads(backend,8);
    if(!ggml_cpu_has_neon()||!ggml_cpu_has_matmul_int8())refuse("original NEON/i8mm8x8 selection unavailable");
    ggml_backend_buffer_type_t weight_type=ggml_backend_cpu_repack_buffer_type();
    if(!weight_type||strcmp(ggml_backend_buft_name(weight_type),"CPU_REPACK"))refuse("explicit CPU_REPACK identity");
    struct ggml_init_params init={sizeof(graph_arena),graph_arena,true};
    ggml_context * context=ggml_init(init);
    if(!context)refuse("bounded graph context allocation");
    ggml_tensor * w=ggml_new_tensor_2d(context,GGML_TYPE_Q5_K,N,8);
    ggml_tensor * x=ggml_new_tensor_2d(context,GGML_TYPE_F32,N,1);
    ggml_tensor * y=ggml_mul_mat(context,w,x);
    ggml_set_name(w,"selected_output_weight_8_rows");
    ggml_set_name(x,"captured_selected_norm_one_column");
    ggml_set_name(y,"bounded_CPU_REPACK_result");
    ggml_backend_buffer_t wb=ggml_backend_buft_alloc_buffer(weight_type,sizeof(group));
    ggml_backend_buffer_t xb=ggml_backend_buft_alloc_buffer(ggml_backend_cpu_buffer_type(),sizeof(norms[0]));
    ggml_backend_buffer_t yb=ggml_backend_buft_alloc_buffer(ggml_backend_cpu_buffer_type(),8*sizeof(float));
    if(!wb||!xb||!yb)refuse("bounded explicit CPU buffer allocation");
    if(ggml_backend_buffer_get_size(wb)!=sizeof(group)||ggml_backend_buffer_get_size(xb)!=sizeof(norms[0])||
       ggml_backend_buffer_get_size(yb)!=8*sizeof(float))refuse("unexpected CPU buffer size");
    if(ggml_backend_tensor_alloc(wb,w,ggml_backend_buffer_get_base(wb))!=GGML_STATUS_SUCCESS||
       ggml_backend_tensor_alloc(xb,x,ggml_backend_buffer_get_base(xb))!=GGML_STATUS_SUCCESS||
       ggml_backend_tensor_alloc(yb,y,ggml_backend_buffer_get_base(yb))!=GGML_STATUS_SUCCESS)refuse("explicit tensor allocation");
    const char * expected_trait="N4ggml3cpu6repack13tensor_traitsI10block_q5_KLx8ELx8EL9ggml_type15EEE";
    if(!w->extra)refuse("CPU_REPACK trait missing; no fallback");
    const char * trait=typeid(*static_cast<ggml::cpu::tensor_traits *>(w->extra)).name();
    if(strcmp(trait,expected_trait))refuse("exact Q5_K8x8/Q8_K trait identity differs; no fallback");
    ggml_cgraph * graph=ggml_new_graph_custom(context,64,false);
    ggml_build_forward_expand(graph,y);
    struct ggml_cplan plan=ggml_graph_plan(graph,8,nullptr);
    if(plan.work_size>GRAPH_WORK_LIMIT||plan.use_ref)refuse("CPU graph work bound or reference override differs");
    if(!ggml_backend_dev_supports_op(ggml_backend_get_device(backend),y))refuse("explicit CPU graph unsupported");
    float graph_logit[SELECTED][2];double math_dot[SELECTED][2];bool oracle_pass=true;
    for(int t=0;t<SELECTED;++t){
        read_exact(fd[0],0,OUTPUT_OFFSET+(off_t)group_starts[t]*ROW_BYTES,group,sizeof(group));
        require_hash(group,sizeof(group),group_hashes[t]);
        int lane=tokens[t]-group_starts[t];if(lane<0||lane>=8)refuse("selected lane bounds");
        require_hash(group[lane],sizeof(group[lane]),row_hashes[t]);
        dequantize_row_q5_K(group[lane],weights,N);
        ggml_backend_tensor_set(w,group,0,sizeof(group));
        for(int j=0;j<2;++j){
            ggml_backend_tensor_set(x,norms[j],0,sizeof(norms[j]));
            if(ggml_backend_graph_compute(backend,graph)!=GGML_STATUS_SUCCESS)refuse("explicit CPU graph compute failed; no fallback");
            float values[8];ggml_backend_tensor_get(y,values,0,sizeof(values));
            for(float value:values)if(!isfinite(value))refuse("nonfinite CPU graph output");
            graph_logit[t][j]=values[lane];math_dot[t][j]=mathematical_dot(weights,norms[j]);
        }
        oracle_pass=oracle_pass&&bits(graph_logit[t][0])==bits(recorded[t][0]);
    }
    for(int i=0;i<5;++i){recheck(fd[i],i);if(close(fd[i]))refuse("input close");}
    printf("{\n\"scope\":\"explicit bounded CPU_REPACK8x8 graph control; historical operator identity unproven\",\n");
    printf("\"CPU_backend\":true,\"weight_buffer\":\"CPU_REPACK\",\"actual_trait\":\"%s\",\n",trait);
    printf("\"actual_NEON\":true,\"actual_i8mm\":true,\"graph_input_columns\":1,\"weight_rows\":8,\"threads\":8,\n");
    printf("\"graph_arena_bytes\":%zu,\"graph_work_bytes\":%zu,\"graph_work_limit_bytes\":%zu,\"logical_limit_bytes\":%zu,\n",sizeof(graph_arena),plan.work_size,GRAPH_WORK_LIMIT,LOGICAL_LIMIT);
    printf("\"GPU_initializations\":0,\"GPU_requests\":0,\"full_model_inference_requests\":0,\"bounded_CPU_graph_calls\":6,\n");
    printf("\"model_row_bytes_read\":84480,\"norm_bytes_read\":40960,\"recorded_logit_bytes_read\":24,\n");
    printf("\"CPU_oracle_all_selected_bitwise\":%s,\"interpret_shared_route_residuals\":%s,\n\"rows\":[\n",oracle_pass?"true":"false",oracle_pass?"true":"false");
    for(int t=0;t<SELECTED;++t){
        printf("{\"token\":%d,\"group_start\":%d,\"selected_lane\":%d,\"recorded_CPU_logit\":%.17g,\"recorded_CUDA_logit\":%.17g,",tokens[t],group_starts[t],tokens[t]-group_starts[t],(double)recorded[t][0],(double)recorded[t][1]);
        printf("\"explicit_graph_CPU_norm\":%.17g,\"explicit_graph_CUDA_norm\":%.17g,\"CPU_oracle_bits_equal\":%s,",(double)graph_logit[t][0],(double)graph_logit[t][1],bits(graph_logit[t][0])==bits(recorded[t][0])?"true":"false");
        printf("\"dequantized_F32_dot_CPU_norm_f64\":%.17g,\"dequantized_F32_dot_CUDA_norm_f64\":%.17g,",math_dot[t][0],math_dot[t][1]);
        printf("\"shared_explicit_graph_hidden_contribution\":%.17g,\"recorded_CUDA_minus_explicit_graph_CUDA_norm\":%.17g}%s\n",(double)graph_logit[t][1]-(double)graph_logit[t][0],(double)recorded[t][1]-(double)graph_logit[t][1],t+1==SELECTED?"":",");
    }
    printf("]\n}\n");
    ggml_backend_buffer_free(yb);ggml_backend_buffer_free(xb);ggml_backend_buffer_free(wb);
    ggml_free(context);ggml_backend_free(backend);
    return oracle_pass?0:2;
}
