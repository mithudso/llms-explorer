package main

import (
	"bytes"
	"context"
	"encoding/json"
	"github.com/ollama/ollama/mlxrunner"
	"github.com/ollama/ollama/mlxrunner/tokenizer"
	"math"
	"reflect"
	"testing"

	"github.com/ollama/ollama/mlx"
	"github.com/ollama/ollama/mlxrunner/cache"
)

func TestPrefixDigestMatchesPythonProtocol(t *testing.T) {
	// Computed independently with hashlib and struct.pack('>I', token).
	cases := []struct {
		ids  []int32
		want string
	}{
		{nil, "daccfff9f1926910430e8b275ed00379269cd0a25b7263f082b150aac1f22d58"},
		{[]int32{2, 105, 106}, "43f208afe60c5cf7b0d8210e41b270e42b3d268aeb061e18adfeb84827f88383"},
	}
	for _, tc := range cases {
		if got := prefixDigest(tc.ids); got != tc.want {
			t.Fatalf("prefixDigest(%v)=%s want %s", tc.ids, got, tc.want)
		}
	}
	if prefixDigest([]int32{1, 23}) == prefixDigest([]int32{12, 3}) {
		t.Fatal("ambiguous token concatenation")
	}
}
func TestCanonicalTokenizerJSON(t *testing.T) {
	// Retain Unicode including U+2028 and literal escape text; Python ensure_ascii=False does too.
	source := []byte("{\"z\":null,\"a\":\"<é>\\n\\\\u003c\u2028\",\"b\":[2,true]}")
	var value any
	decoder := json.NewDecoder(bytes.NewReader(source))
	decoder.UseNumber()
	if err := decoder.Decode(&value); err != nil {
		t.Fatal(err)
	}
	var got bytes.Buffer
	if err := canonicalJSON(value, &got); err != nil {
		t.Fatal(err)
	}
	want := "{\"a\":\"<é>\\n\\\\u003c\u2028\",\"b\":[2,true],\"z\":null}"
	if got.String() != want {
		t.Fatalf("canonical JSON %q want %q", got.String(), want)
	}
}
func TestFullSessionStateMustMatch(t *testing.T) {
	st := &session{id: "test", prefix: []int32{2, 105}, revision: 3}
	svc := &service{sessions: map[string]*session{"test": st}}
	state := st.state()
	if _, err := svc.findSession(rpcRequest{State: &state}); err != nil {
		t.Fatal(err)
	}
	for _, changed := range []wireState{
		{"test", 2, state.PrefixDigest, 2},
		{"test", 3, "wrong", 2},
		{"test", 3, state.PrefixDigest, 3},
		{"missing", 3, state.PrefixDigest, 2},
	} {
		if _, err := svc.findSession(rpcRequest{State: &changed}); err == nil {
			t.Fatalf("accepted stale state %#v", changed)
		}
	}
	if _, err := svc.findSession(rpcRequest{State: &state, SessionID: "different"}); err == nil {
		t.Fatal("accepted conflicting session IDs")
	}
}
func TestVerificationAndCommitAtContextBoundary(t *testing.T) {
	if err := validateVerificationCapacity(15, 1, 16); err != nil {
		t.Fatal("last valid proposal rejected", err)
	}
	if err := validateVerificationCapacity(15, 2, 16); err == nil {
		t.Fatal("out-of-context proposal accepted")
	}
	noEOS := func(int32) bool { return false }
	// The bonus must be omitted when it would exceed the output capacity.
	if _, err := validateCommitTokens([]int32{7}, []int32{7, 8}, []int32{7}, 15, 16, noEOS); err != nil {
		t.Fatal(err)
	}
	if _, err := validateCommitTokens([]int32{7}, []int32{7, 8}, []int32{7, 8}, 15, 16, noEOS); err == nil {
		t.Fatal("bonus beyond context accepted")
	}
}
func TestInspectionIDsAreBoundedBeforeNativeEvaluation(t *testing.T) {
	for _, tc := range []struct {
		name string
		ids  []int32
		ok   bool
	}{
		{"absent", nil, true},
		{"maximum including edge IDs", []int32{0, 15, 1, 2, 3, 4, 5, 6}, true},
		{"too many", []int32{0, 1, 2, 3, 4, 5, 6, 7, 8}, false},
		{"negative ID", []int32{-1}, false},
		{"ID at vocabulary bound", []int32{16}, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			if err := validateInspectIDs(tc.ids, 16); (err == nil) != tc.ok {
				t.Fatalf("error=%v want success=%v", err, tc.ok)
			}
		})
	}
}
func TestInspectionPreservesRowMajorScoresAndSerializesSuppression(t *testing.T) {
	ids := []int32{15, 7}
	scores := []float32{2.5, 1.25, float32(math.Inf(-1)), float32(math.NaN()), 3, float32(math.Inf(1))}
	reply, err := inspectionResult(ids, 3, scores)
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(reply["inspect_shape"], []int{3, 2}) || !reflect.DeepEqual(reply["inspect_ids"], ids) {
		t.Fatal("inspection row/column identity changed")
	}
	if !reflect.DeepEqual(reply["inspect_logits"], []any{float32(2.5), float32(1.25), nil, nil, float32(3), nil}) {
		t.Fatal("inspection score order changed")
	}
	if !reflect.DeepEqual(reply["inspect_nonfinite"], map[int]string{2: "-inf", 3: "nan", 5: "+inf"}) {
		t.Fatal("nonfinite classifications changed")
	}
	if _, err := json.Marshal(reply); err != nil {
		t.Fatal("suppressed logits cannot be encoded as JSON", err)
	}
	ids[0] = 0
	if reply["inspect_ids"].([]int32)[0] != 15 {
		t.Fatal("response aliases caller ID buffer")
	}
	if _, err := inspectionResult([]int32{1, 2}, 2, []float32{1, 2}); err == nil {
		t.Fatal("truncated score matrix accepted")
	}
}
func TestCommitIsOnlyExactGreedyPrefix(t *testing.T) {
	eos := func(id int32) bool { return id == 9 }
	cases := []struct {
		name               string
		draft, target, out []int32
		want               int
		ok                 bool
	}{
		{"all accepted", []int32{3, 4}, []int32{3, 4, 5}, []int32{3, 4, 5}, 2, true},
		{"partial correction", []int32{3, 8}, []int32{3, 4, 5}, []int32{3, 4}, 1, true},
		{"first rejection", []int32{8, 9}, []int32{3, 4, 5}, []int32{3}, 0, true},
		{"truncated accepted", []int32{3, 4}, []int32{3, 4, 5}, []int32{3}, 1, true},
		{"accepted EOS", []int32{3, 9}, []int32{3, 9, 5}, []int32{3, 9}, 2, true},
		{"tokens after EOS", []int32{3, 9}, []int32{3, 9, 5}, []int32{3, 9, 5}, 0, false},
		{"bad correction", []int32{3, 8}, []int32{3, 4, 5}, []int32{3, 8}, 0, false},
		{"empty commit", nil, []int32{3}, nil, 0, false},
		{"bad target rows", []int32{3}, []int32{3}, []int32{3}, 0, false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got, err := validateCommitTokens(tc.draft, tc.target, tc.out, 2, 32, eos)
			if (err == nil) != tc.ok {
				t.Fatalf("error=%v expected success=%v", err, tc.ok)
			}
			if tc.ok && got != tc.want {
				t.Fatalf("accepted=%d want %d", got, tc.want)
			}
		})
	}
}

type fakeSnapshot struct{ closed bool }

func (s *fakeSnapshot) Size() int                    { return 1 }
func (s *fakeSnapshot) SetMaterializeHook(func(int)) {}
func (s *fakeSnapshot) Close()                       { s.closed = true }

type fakeCache struct {
	offset   int
	live     bool
	restored cache.Snapshot
}

func (c *fakeCache) State() []*mlx.Array             { return nil }
func (c *fakeCache) Free()                           {}
func (c *fakeCache) Offset() int                     { return c.offset }
func (c *fakeCache) Snapshot(int) cache.Snapshot     { return &fakeSnapshot{} }
func (c *fakeCache) PrepareSnapshots([]int)          {}
func (c *fakeCache) TakeSnapshots() []cache.Snapshot { return nil }
func (c *fakeCache) Restore(s cache.Snapshot, target int) bool {
	if s == nil && !c.live {
		return false
	}
	if v, ok := s.(*fakeSnapshot); ok && v.closed {
		return false
	}
	c.offset = target
	c.restored = s
	return true
}
func (c *fakeCache) Merge(a, b cache.Snapshot) cache.Snapshot                       { return a }
func (c *fakeCache) Split(a cache.Snapshot, _ int) (cache.Snapshot, cache.Snapshot) { return nil, a }
func TestRollbackUsesCapturedWindowWhenLiveRewindFails(t *testing.T) {
	for _, live := range []bool{true, false} {
		t.Run(map[bool]string{true: "live", false: "captured rotating window"}[live], func(t *testing.T) {
			c := &fakeCache{offset: 1030, live: live}
			snaps := []cache.Snapshot{&fakeSnapshot{}, &fakeSnapshot{}, &fakeSnapshot{}}
			selected := snaps[1]
			st := &session{caches: []cache.Cache{c}, pending: &verification{before: 1027, snapshots: [][]cache.Snapshot{snaps}}}
			if err := (&service{}).restore(st, 1); err != nil {
				t.Fatal(err)
			}
			if c.offset != 1028 {
				t.Fatalf("cache offset=%d", c.offset)
			}
			if !live && c.restored != selected {
				t.Fatal("captured window was not used")
			}
			for _, snap := range snaps {
				if snap != nil && !snap.(*fakeSnapshot).closed {
					t.Fatal("snapshot leak")
				}
			}
		})
	}
}
func TestRestoreRejectsMissingCheckpoint(t *testing.T) {
	c := &fakeCache{offset: 10}
	st := &session{caches: []cache.Cache{c}, pending: &verification{before: 7, snapshots: [][]cache.Snapshot{{nil}}}}
	if err := (&service{}).restore(st, 2); err == nil {
		t.Fatal("missing checkpoint silently accepted")
	}
	if !reflect.DeepEqual(c.offset, 10) {
		t.Fatal("cache changed before checkpoint validation")
	}
}

func TestDecodeReportsPartialUTF8BeforeJSONRepair(t *testing.T) {
	tok, err := tokenizer.LoadFromBytes([]byte(`{"model":{"type":"BPE","vocab":{"Ã":0,"©":1},"merges":[]}}`))
	if err != nil {
		t.Fatal(err)
	}
	svc := &service{runner: &mlxrunner.Runner{Tokenizer: tok}}
	partial, err := svc.dispatch(rpcRequest{Op: "decode", TokenIDs: []int32{0}}, context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if partial["valid_utf8"] != false {
		t.Fatal("partial byte sequence was reported as valid UTF8")
	}
	complete, err := svc.dispatch(rpcRequest{Op: "decode", TokenIDs: []int32{0, 1}}, context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if complete["valid_utf8"] != true || complete["text"] != "é" {
		t.Fatalf("complete decode=%#v", complete)
	}
}
