// Pending separately authorized CPU-only test of the exact proposed atomic ledger.
#include <stdexcept>
#include <thread>
#include <atomic>
#include <cstdio>
#include <limits>
struct Refusal {};
#define GGML_CUDA_NO_VMM
#define GGML_CUDA_MAX_STREAMS 8
#define GGML_ABORT(...) throw Refusal()
#include "llmsx_aggregate_scratch.hpp"
static unsigned controls=0;
static void check(bool ok) { if (!ok) { throw std::runtime_error("atomic ledger control failed"); } ++controls; }
static void rejected_release(size_t bytes) { bool refused=false;try {llmsx_scratch::release(bytes);}catch(const Refusal &){refused=true;}check(refused); }
int main() {
 using namespace llmsx_scratch;
 check(reserved.load()==0);
 check(!reserve(0));check(!reserve(limit+1));check(!reserve(std::numeric_limits<size_t>::max()));
 check(reserve(limit));check(!reserve(1));check(reserved.load()==limit);release(limit);check(reserved.load()==0);
 rejected_release(1);check(reserve(7));rejected_release(8);rejected_release(0);check(reserved.load()==7);release(7);rejected_release(7);
 // Every contender waits for a simultaneous start, then races one capacity
 // reservation. No contender releases until all attempts have joined.
 std::atomic<unsigned> ready{0};std::atomic<bool> go{false};bool won[16]={};std::thread workers[16];
 for(unsigned i=0;i<16;++i){workers[i]=std::thread([&,i]{ready.fetch_add(1);while(!go.load()){std::this_thread::yield();}won[i]=reserve(cublas_per_context);});}
 while(ready.load()!=16){std::this_thread::yield();}go.store(true);
 for(auto &t:workers)t.join();unsigned wins=0;for(bool b:won)wins+=b;
 check(wins==8);check(reserved.load()==limit);check(peak.load()==limit);
 for(bool b:won)if(b)release(cublas_per_context);check(reserved.load()==0);
 // A prepaid context consumes capacity while arbitrary pools hold reservations.
 check(reserve(cublas_per_context));constexpr size_t matrix=374341632;
 for(unsigned i=0;i<5;++i)check(reserve(matrix));check(!reserve(matrix));check(reserved.load()==2140143616ull);
 for(unsigned i=0;i<5;++i)release(matrix);release(cublas_per_context);check(reserved.load()==0);
 std::printf("{\"exact_header_atomic_controls\":%u,\"passed\":true,\"GPU_initializations\":0,\"GPU_requests\":0}\n",controls);
}
