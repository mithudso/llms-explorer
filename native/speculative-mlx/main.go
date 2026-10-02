// speculative-mlx exposes token-level greedy verification using Ollama's native MLX model.
// It never changes Ollama manifests, provider configuration, or running services.
package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"math"
	"net"
	"net/http"
	"os"
	"os/signal"
	"sort"
	"strings"
	"syscall"
	"time"
	"unicode/utf8"

	"github.com/ollama/ollama/manifest"
	"github.com/ollama/ollama/mlx"
	"github.com/ollama/ollama/mlx/mlxthread"
	"github.com/ollama/ollama/mlxrunner"
	"github.com/ollama/ollama/mlxrunner/batch"
	"github.com/ollama/ollama/mlxrunner/cache"
	modeltypes "github.com/ollama/ollama/types/model"
)

const sourceRevision = "cc4069396f3ad2c370c53eed2e4a42ac13adab84"
const mlxCSourceRevision = "ebc88f10caa1b625e6b581437a8dea6df8a70085"
const canonicalModel = "llmsx-research-gemma31-mlx"
const canonicalManifest = "559e7d6999dbf031c7f842e84257eea6d43a8adcb6ff90a727baa05d4a5e6b0d"

type rpcRequest struct {
	Op               string     `json:"op"`
	SessionID        string     `json:"session_id"`
	PrefixIDs        []int32    `json:"prefix_ids"`
	TokenIDs         []int32    `json:"token_ids"`
	ProposedIDs      []int32    `json:"proposed_ids"`
	InspectIDs       []int32    `json:"inspect_ids"`
	Text             string     `json:"text"`
	AddBOS           *bool      `json:"add_bos"`
	AcceptedCount    *int       `json:"accepted_count"`
	ExpectedRevision *uint64    `json:"expected_revision"`
	State            *wireState `json:"state"`
}

type wireState struct {
	SessionID    string `json:"session_id"`
	RoundID      uint64 `json:"round_id"`
	PrefixDigest string `json:"prefix_digest"`
	Position     int    `json:"position"`
}

func prefixDigest(ids []int32) string {
	h := sha256.New()
	_, _ = h.Write([]byte("llmsx-token-prefix-v1\x00"))
	var value [4]byte
	for _, id := range ids {
		binary.BigEndian.PutUint32(value[:], uint32(id))
		_, _ = h.Write(value[:])
	}
	return hex.EncodeToString(h.Sum(nil))
}
func (st *session) state() wireState {
	return wireState{st.id, st.revision, prefixDigest(st.prefix), len(st.prefix)}
}

// Python-compatible json.dumps(sort_keys=True, ensure_ascii=False, separators=(",",":")).
// Tokenizer files use finite numeric metadata and valid Unicode strings.
func canonicalJSON(value any, w io.Writer) error {
	switch v := value.(type) {
	case nil:
		_, _ = io.WriteString(w, "null")
	case bool:
		if v {
			_, _ = io.WriteString(w, "true")
		} else {
			_, _ = io.WriteString(w, "false")
		}
	case json.Number:
		_, _ = io.WriteString(w, string(v))
	case string:
		_, _ = io.WriteString(w, "\"")
		for _, r := range v {
			switch r {
			case '"':
				_, _ = io.WriteString(w, "\\\"")
			case '\\':
				_, _ = io.WriteString(w, "\\\\")
			case '\b':
				_, _ = io.WriteString(w, "\\b")
			case '\f':
				_, _ = io.WriteString(w, "\\f")
			case '\n':
				_, _ = io.WriteString(w, "\\n")
			case '\r':
				_, _ = io.WriteString(w, "\\r")
			case '\t':
				_, _ = io.WriteString(w, "\\t")
			default:
				if r < 32 {
					_, _ = fmt.Fprintf(w, "\\u%04x", r)
				} else {
					_, _ = io.WriteString(w, string(r))
				}
			}
		}
		_, _ = io.WriteString(w, "\"")
	case []any:
		_, _ = io.WriteString(w, "[")
		for i, item := range v {
			if i > 0 {
				_, _ = io.WriteString(w, ",")
			}
			if err := canonicalJSON(item, w); err != nil {
				return err
			}
		}
		_, _ = io.WriteString(w, "]")
	case map[string]any:
		keys := make([]string, 0, len(v))
		for key := range v {
			keys = append(keys, key)
		}
		sort.Strings(keys)
		_, _ = io.WriteString(w, "{")
		for i, key := range keys {
			if i > 0 {
				_, _ = io.WriteString(w, ",")
			}
			_ = canonicalJSON(key, w)
			_, _ = io.WriteString(w, ":")
			if err := canonicalJSON(v[key], w); err != nil {
				return err
			}
		}
		_, _ = io.WriteString(w, "}")
	default:
		return fmt.Errorf("unsupported tokenizer value %T", value)
	}
	return nil
}
func tokenizerMetadata(m *manifest.Manifest) (string, []int32, error) {
	data, err := m.ReadConfig("tokenizer.json")
	if err != nil {
		return "", nil, err
	}
	var document map[string]any
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.UseNumber()
	if err := decoder.Decode(&document); err != nil {
		return "", nil, err
	}
	hash := sha256.New()
	if err := canonicalJSON(document, hash); err != nil {
		return "", nil, err
	}
	var special []int32
	if tokens, ok := document["added_tokens"].([]any); ok {
		for _, item := range tokens {
			entry, ok := item.(map[string]any)
			if !ok {
				continue
			}
			if entry["special"] != true {
				continue
			}
			number, ok := entry["id"].(json.Number)
			if !ok {
				continue
			}
			id, err := number.Int64()
			if err != nil || id < 0 || id > 2147483647 {
				return "", nil, errors.New("invalid tokenizer special ID")
			}
			special = append(special, int32(id))
		}
	}
	sort.Slice(special, func(i, j int) bool { return special[i] < special[j] })
	return hex.EncodeToString(hash.Sum(nil)), special, nil
}

type verification struct {
	before      int
	proposals   []int32
	predictions []int32
	snapshots   [][]cache.Snapshot
	duration    time.Duration
}

type session struct {
	id       string
	prefix   []int32
	caches   []cache.Cache
	pending  *verification
	revision uint64
	done     bool
}

type service struct {
	runner       *mlxrunner.Runner
	worker       *mlxthread.Thread
	model        string
	manifest     string
	tokenizer    string
	fingerprint  string
	special      []int32
	maxContext   int
	maxDraft     int
	maxSessions  int
	prefillChunk int
	sessions     map[string]*session // Accessed only on worker's locked OS thread.
	library      string
}

type apiError struct {
	status  int
	message string
}

func (e *apiError) Error() string { return e.message }
func fail(status int, format string, args ...any) error {
	return &apiError{status, fmt.Sprintf(format, args...)}
}

func (s *service) metadata() map[string]any {
	return map[string]any{
		"backend": "ollama-native-mlx", "backend_id": "ollama-native-mlx-target", "model_id": s.model, "protocol_version": 1, "model": s.model,
		"tokenizer_fingerprint": s.fingerprint, "special_token_ids": s.special, "supports_propose": false, "supports_verify": true, "supports_rollback": true, "verification_mode": "greedy-block", "model_loaded": true,
		"source_revision": sourceRevision, "manifest_sha256": s.manifest,
		"tokenizer_sha256": s.tokenizer, "mlx_library": s.library, "mlx_version": mlx.Version(), "mlx_c_source_revision": mlxCSourceRevision,
		"vocab_size": s.runner.Tokenizer.VocabSize(), "eos_ids": s.runner.Tokenizer.EOSTokens(), "tokenizer_add_bos": s.runner.Tokenizer.AddBOS(),
		"max_context": s.maxContext, "max_draft": s.maxDraft, "sessions": len(s.sessions),
		"capabilities": map[string]bool{"greedy_block_verify": true, "cache_rollback": true, "persistent_sessions": true, "stochastic": false, "bundled_assistant_decode": false},
	}
}

func validIDs(ids []int32, vocab int) error {
	for _, id := range ids {
		if id < 0 || int(id) >= vocab {
			return fail(http.StatusBadRequest, "token ID %d is outside vocabulary", id)
		}
	}
	return nil
}
func cacheStates(cs []cache.Cache) []*mlx.Array {
	var arrays []*mlx.Array
	for _, c := range cs {
		if c != nil {
			arrays = append(arrays, c.State()...)
		}
	}
	return arrays
}
func cachePosition(cs []cache.Cache) (int, error) {
	offset := -1
	for _, c := range cs {
		if c == nil {
			continue
		}
		if offset < 0 {
			offset = c.Offset()
		} else if c.Offset() != offset {
			return 0, fmt.Errorf("cache offsets diverged: %d and %d", offset, c.Offset())
		}
	}
	if offset < 0 {
		return 0, errors.New("model supplied no cache slots")
	}
	return offset, nil
}
func closeSnapshots(snaps [][]cache.Snapshot) {
	for _, row := range snaps {
		for _, snap := range row {
			if snap != nil {
				snap.Close()
			}
		}
	}
}
func (s *service) closeSession(id string) {
	st := s.sessions[id]
	if st == nil {
		return
	}
	if st.pending != nil {
		closeSnapshots(st.pending.snapshots)
		st.pending = nil
	}
	for _, c := range st.caches {
		if c != nil {
			for _, snap := range c.TakeSnapshots() {
				if snap != nil {
					snap.Close()
				}
			}
			c.Free()
		}
	}
	delete(s.sessions, id)
	mlx.ClearCache()
}
func (s *service) shutdown() {
	for id := range s.sessions {
		s.closeSession(id)
	}
	s.runner.Close()
	mlx.ClearCache()
}

// forward evaluates only this model and this session's independent cache slots.
func (s *service) forward(st *session, ids []int32, offset int, logits bool, inspect []int32) ([]int32, []float32) {
	var predictions []int32
	var scores []float32
	mlx.Scoped(func() {
		result := mlx.ScopedArrays(func() []*mlx.Array {
			hidden, _ := s.runner.Model.Forward(&batch.Batch{
				InputIDs: mlx.FromValues(ids, 1, len(ids)), SeqOffsets: []int32{int32(offset)}, SeqQueryLens: []int32{int32(len(ids))},
			}, st.caches)
			if !logits {
				return nil
			}
			output := s.runner.Model.Unembed(hidden)
			results := []*mlx.Array{output.Argmax(-1, false).AsType(mlx.DTypeInt32)}
			if len(inspect) > 0 {
				selected := output.TakeAxis(mlx.FromValues(inspect, len(inspect)), -1).AsType(mlx.DTypeFloat32)
				results = append(results, mlx.Contiguous(selected, false))
			}
			return results
		})
		mlx.Eval(append(result, cacheStates(st.caches)...)...)
		if logits {
			predictions = append([]int32(nil), result[0].Ints()...)
			if len(inspect) > 0 {
				scores = append([]float32(nil), result[1].Floats()...)
			}
		}
	})
	return predictions, scores
}
func (s *service) open(req rpcRequest, ctx context.Context) (map[string]any, error) {
	if len(s.sessions) >= s.maxSessions {
		return nil, fail(http.StatusConflict, "maximum active sessions reached; close an existing session")
	}
	prefix := req.PrefixIDs
	if len(prefix) == 0 {
		prefix = req.TokenIDs
	}
	if len(prefix) == 0 {
		return nil, fail(http.StatusBadRequest, "prefix_ids must contain at least one token")
	}
	if len(prefix) >= s.maxContext {
		return nil, fail(http.StatusBadRequest, "prefix length must be below max_context")
	}
	if err := validIDs(prefix, s.runner.Tokenizer.VocabSize()); err != nil {
		return nil, err
	}
	random := make([]byte, 16)
	if _, err := rand.Read(random); err != nil {
		return nil, err
	}
	id := req.SessionID
	if id == "" {
		id = hex.EncodeToString(random)
	}
	if len(id) > 128 || strings.ContainsAny(id, "/\\\x00") {
		return nil, fail(http.StatusBadRequest, "invalid session_id")
	}
	if _, exists := s.sessions[id]; exists {
		return nil, fail(http.StatusConflict, "session_id already exists")
	}
	st := &session{id: id, prefix: append([]int32(nil), prefix...), caches: s.runner.Model.NewCaches()}
	s.sessions[st.id] = st
	success := false
	defer func() {
		if !success {
			s.closeSession(st.id)
		}
	}()
	started := time.Now()
	// The last committed token remains pending. The verifier forwards it fused with proposals.
	for position := 0; position < len(prefix)-1; {
		if err := ctx.Err(); err != nil {
			return nil, err
		}
		end := min(position+s.prefillChunk, len(prefix)-1)
		s.forward(st, prefix[position:end], position, false, nil)
		position = end
		mlx.ClearCache()
	}
	if position, err := cachePosition(st.caches); err != nil || position != len(prefix)-1 {
		return nil, fmt.Errorf("prefill cache position mismatch: got %d wanted %d: %v", position, len(prefix)-1, err)
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	success = true
	return map[string]any{"session_id": st.id, "revision": st.revision, "position": len(st.prefix), "state": st.state(), "prefill_ms": float64(time.Since(started).Microseconds()) / 1000}, nil
}
func (s *service) findSession(req rpcRequest) (*session, error) {
	id := req.SessionID
	if req.State != nil {
		if id != "" && id != req.State.SessionID {
			return nil, fail(http.StatusBadRequest, "session_id and state disagree")
		}
		id = req.State.SessionID
	}
	st := s.sessions[id]
	if st == nil {
		return nil, fail(http.StatusNotFound, "unknown session_id")
	}
	if req.State != nil && *req.State != st.state() {
		return nil, fail(http.StatusConflict, "request state disagrees with committed session")
	}
	if req.ExpectedRevision != nil && *req.ExpectedRevision != st.revision {
		return nil, fail(http.StatusConflict, "session revision changed: current revision %d", st.revision)
	}
	return st, nil
}
func validateVerificationCapacity(prefixLength, proposalCount, maxContext int) error {
	if prefixLength+proposalCount > maxContext {
		return fail(http.StatusBadRequest, "verification would exceed max_context")
	}
	return nil
}
func (s *service) verify(req rpcRequest) (map[string]any, error) {
	if req.State == nil {
		return nil, fail(http.StatusBadRequest, "verify requires complete state")
	}
	st, err := s.findSession(req)
	if err != nil {
		return nil, err
	}
	if st.done {
		return nil, fail(http.StatusConflict, "session reached EOS")
	}
	if st.pending != nil {
		return nil, fail(http.StatusConflict, "verify result must be committed or rolled back before another verify")
	}
	proposals := req.ProposedIDs
	if proposals == nil {
		proposals = req.TokenIDs
	}
	if len(proposals) > s.maxDraft {
		return nil, fail(http.StatusBadRequest, "proposal block exceeds max_draft")
	}
	if err := validateVerificationCapacity(len(st.prefix), len(proposals), s.maxContext); err != nil {
		return nil, err
	}
	if err := validIDs(proposals, s.runner.Tokenizer.VocabSize()); err != nil {
		return nil, err
	}
	if err := validateInspectIDs(req.InspectIDs, s.runner.Tokenizer.VocabSize()); err != nil {
		return nil, err
	}
	before, err := cachePosition(st.caches)
	if err != nil {
		return nil, err
	}
	if before != len(st.prefix)-1 {
		return nil, fmt.Errorf("cache position %d differs from pending-prefix position %d", before, len(st.prefix)-1)
	}
	offsets := make([]int, len(proposals)+2)
	// Capture the pre-write boundary too, so rollback can undo the current token.
	for i := range offsets {
		offsets[i] = before + i
	}
	for _, c := range st.caches {
		if c != nil {
			c.PrepareSnapshots(offsets)
		}
	}
	v := &verification{before: before, proposals: append([]int32(nil), proposals...)}
	st.pending = v // If model evaluation panics, the HTTP recovery invalidates this session.
	started := time.Now()
	input := append([]int32{st.prefix[len(st.prefix)-1]}, proposals...)
	var scores []float32
	v.predictions, scores = s.forward(st, input, before, true, req.InspectIDs)
	v.duration = time.Since(started)
	v.snapshots = make([][]cache.Snapshot, len(st.caches))
	for i, c := range st.caches {
		if c != nil {
			v.snapshots[i] = c.TakeSnapshots()
		}
	}
	if len(v.predictions) != len(proposals)+1 {
		return nil, fmt.Errorf("target returned %d prediction rows for %d input tokens", len(v.predictions), len(input))
	}
	maxAccepted := 0
	for i, id := range proposals {
		if id != v.predictions[i] {
			break
		}
		maxAccepted++
	}
	reply := map[string]any{
		"session_id": st.id, "revision": st.revision, "position": len(st.prefix),
		"state": st.state(), "target_ids": v.predictions, "accepted_count": maxAccepted, "next_token_id": v.predictions[maxAccepted],
		"verify_ms": float64(v.duration.Microseconds()) / 1000, "target_forward_count": 1,
	}
	if len(req.InspectIDs) > 0 {
		inspection, err := inspectionResult(req.InspectIDs, len(v.predictions), scores)
		if err != nil {
			return nil, err
		}
		for key, value := range inspection {
			reply[key] = value
		}
	}
	return reply, nil
}

// Inspection reads a bounded set of columns from the already computed logits.
func validateInspectIDs(ids []int32, vocabSize int) error {
	if len(ids) > 8 {
		return fail(http.StatusBadRequest, "inspect_ids exceeds the 8-token limit")
	}
	return validIDs(ids, vocabSize)
}

func inspectionResult(ids []int32, rows int, scores []float32) (map[string]any, error) {
	if rows < 1 || len(ids) < 1 || len(scores) != rows*len(ids) {
		return nil, fmt.Errorf("inspection returned %d scores for %d rows and %d columns", len(scores), rows, len(ids))
	}
	values := make([]any, len(scores))
	nonfinite := make(map[int]string)
	for i, score := range scores {
		switch {
		case math.IsNaN(float64(score)):
			nonfinite[i] = "nan"
		case math.IsInf(float64(score), -1):
			nonfinite[i] = "-inf"
		case math.IsInf(float64(score), 1):
			nonfinite[i] = "+inf"
		default:
			values[i] = score
		}
	}
	reply := map[string]any{"inspect_ids": append([]int32(nil), ids...), "inspect_shape": []int{rows, len(ids)}, "inspect_logits": values}
	if len(nonfinite) > 0 {
		reply["inspect_nonfinite"] = nonfinite
	}
	return reply, nil
}

// restore retains only the cache prefix ending at a captured absolute position.
func (s *service) restore(st *session, index int) error {
	v := st.pending
	target := v.before + index
	for i, c := range st.caches {
		if c == nil {
			continue
		}
		if len(v.snapshots[i]) <= index {
			return fmt.Errorf("missing rollback snapshot for cache %d at index %d", i, index)
		}
		// Drop unused lazy snapshots before restore, avoiding needless materialization.
		for j, snap := range v.snapshots[i] {
			if snap != nil && j != index {
				snap.Close()
				v.snapshots[i][j] = nil
			}
		}
		if !c.Restore(nil, target) && !c.Restore(v.snapshots[i][index], target) {
			return fmt.Errorf("cache %d cannot restore offset %d", i, target)
		}
	}
	closeSnapshots(v.snapshots)
	v.snapshots = nil
	position, err := cachePosition(st.caches)
	if err != nil {
		return err
	}
	if position != target {
		return fmt.Errorf("restored cache position %d differs from %d", position, target)
	}
	return nil
}

// validateCommitTokens accepts only a bounded prefix of the target-certified greedy run.
func validateCommitTokens(proposals, predictions, emitted []int32, prefixLength, maxContext int, isEOS func(int32) bool) (int, error) {
	if len(predictions) != len(proposals)+1 {
		return 0, errors.New("invalid target prediction count")
	}
	maxAccepted := 0
	for i, id := range proposals {
		if id != predictions[i] {
			break
		}
		maxAccepted++
	}
	expected := append([]int32(nil), proposals[:maxAccepted]...)
	expected = append(expected, predictions[maxAccepted])
	if prefixLength+len(emitted) > maxContext {
		return 0, fail(http.StatusBadRequest, "commit would exceed max_context")
	}
	if len(emitted) == 0 || len(emitted) > len(expected) {
		return 0, fail(http.StatusBadRequest, "commit token count is outside verified greedy run")
	}
	for i, id := range emitted {
		if id != expected[i] {
			return 0, fail(http.StatusBadRequest, "committed token disagrees with greedy target at index %d", i)
		}
		if isEOS(id) && i != len(emitted)-1 {
			return 0, fail(http.StatusBadRequest, "commit contains tokens after EOS")
		}
	}
	return min(len(emitted), maxAccepted), nil
}
func (s *service) commit(req rpcRequest) (map[string]any, error) {
	if req.State == nil {
		return nil, fail(http.StatusBadRequest, "commit requires complete state")
	}
	st, err := s.findSession(req)
	if err != nil {
		return nil, err
	}
	v := st.pending
	if v == nil {
		return nil, fail(http.StatusConflict, "no pending verification")
	}
	accepted, err := validateCommitTokens(v.proposals, v.predictions, req.TokenIDs, len(st.prefix), s.maxContext, s.runner.Tokenizer.IsEOS)
	if err != nil {
		return nil, err
	}
	if req.AcceptedCount != nil && *req.AcceptedCount != accepted {
		return nil, fail(http.StatusBadRequest, "accepted_count disagrees with committed greedy run")
	}
	emitted := req.TokenIDs
	// The final emitted token becomes pending. Keep its predecessors from this block.
	if err := s.restore(st, len(emitted)); err != nil {
		return nil, err
	}
	st.prefix = append(st.prefix, emitted...)
	st.done = s.runner.Tokenizer.IsEOS(emitted[len(emitted)-1])
	st.pending = nil
	st.revision++
	// The final emitted token is pending even at EOS, keeping one cache convention.
	if !st.done {
		if pos, err := cachePosition(st.caches); err != nil || pos != len(st.prefix)-1 {
			return nil, fmt.Errorf("commit cache/prefix mismatch at %d: %v", pos, err)
		}
	}
	return map[string]any{"session_id": st.id, "revision": st.revision, "position": len(st.prefix), "done": st.done, "state": st.state(), "cache_offsets": s.offsets(st)}, nil
}
func (s *service) offsets(st *session) []int {
	out := make([]int, len(st.caches))
	for i, c := range st.caches {
		if c != nil {
			out[i] = c.Offset()
		} else {
			out[i] = -1
		}
	}
	return out
}
func (s *service) rollback(req rpcRequest) (map[string]any, error) {
	if req.State == nil {
		return nil, fail(http.StatusBadRequest, "rollback requires complete state")
	}
	st, err := s.findSession(req)
	if err != nil {
		return nil, err
	}
	if st.pending != nil {
		if err := s.restore(st, 0); err != nil {
			return nil, err
		}
		st.pending = nil
	}
	return map[string]any{"session_id": st.id, "revision": st.revision, "position": len(st.prefix), "state": st.state(), "cache_offsets": s.offsets(st)}, nil
}
func (s *service) dispatch(req rpcRequest, ctx context.Context) (map[string]any, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	switch req.Op {
	case "health", "metadata", "describe":
		return s.metadata(), nil
	case "tokenize":
		add := s.runner.Tokenizer.AddBOS()
		if req.AddBOS != nil {
			add = *req.AddBOS
		}
		return map[string]any{"token_ids": s.runner.Tokenizer.Encode(req.Text, add), "tokenizer_sha256": s.tokenizer}, nil
	case "decode":
		if err := validIDs(req.TokenIDs, s.runner.Tokenizer.VocabSize()); err != nil {
			return nil, err
		}
		text := s.runner.Tokenizer.Decode(req.TokenIDs)
		return map[string]any{"text": text, "valid_utf8": utf8.ValidString(text)}, nil
	case "open":
		return s.open(req, ctx)
	case "verify":
		return s.verify(req)
	case "commit":
		return s.commit(req)
	case "rollback":
		return s.rollback(req)
	case "state":
		st, err := s.findSession(req)
		if err != nil {
			return nil, err
		}
		return map[string]any{"session_id": st.id, "revision": st.revision, "prefix_ids": st.prefix, "state": st.state(), "position": len(st.prefix), "pending_verification": st.pending != nil, "done": st.done, "cache_offsets": s.offsets(st)}, nil
	case "close":
		st, err := s.findSession(req)
		if err != nil {
			return nil, err
		}
		s.closeSession(st.id)
		return map[string]any{"closed": true}, nil
	default:
		return nil, fail(http.StatusBadRequest, "unknown op %q", req.Op)
	}
}
func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}
func (s *service) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	req := rpcRequest{}
	var result map[string]any
	requestSessionID := func() string {
		if req.State != nil {
			return req.State.SessionID
		}
		if req.SessionID != "" {
			return req.SessionID
		}
		if result != nil {
			if id, ok := result["session_id"].(string); ok {
				return id
			}
		}
		return ""
	}
	defer func() {
		if recovered := recover(); recovered != nil {
			log.Printf("native verifier failure: %v", recovered)
			// Cache state after a failed native graph must never be reused.
			_ = s.worker.Do(context.Background(), func() error {
				if id := requestSessionID(); id != "" {
					s.closeSession(id)
				}
				return nil
			})
			writeJSON(w, http.StatusInternalServerError, map[string]any{"error": "native verifier failed; session invalidated"})
		}
	}()
	switch {
	case r.Method == "GET" && (r.URL.Path == "/health" || r.URL.Path == "/describe"):
		req.Op = "health"
	case r.Method == "POST" && r.URL.Path == "/rpc":
		decoder := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4<<20))
		decoder.DisallowUnknownFields()
		if err := decoder.Decode(&req); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]any{"error": err.Error()})
			return
		}
	case r.Method == "POST" && (r.URL.Path == "/tokenize" || r.URL.Path == "/decode" || r.URL.Path == "/sessions"):
		decoder := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4<<20))
		decoder.DisallowUnknownFields()
		if err := decoder.Decode(&req); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]any{"error": err.Error()})
			return
		}
		req.Op = strings.TrimPrefix(r.URL.Path, "/")
		if req.Op == "sessions" {
			req.Op = "open"
		}
	case strings.HasPrefix(r.URL.Path, "/sessions/"):
		parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/sessions/"), "/")
		if len(parts) == 1 && r.Method == "DELETE" {
			req.Op = "close"
			req.SessionID = parts[0]
		} else if len(parts) == 2 && r.Method == "POST" {
			decoder := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4<<20))
			decoder.DisallowUnknownFields()
			if err := decoder.Decode(&req); err != nil {
				writeJSON(w, http.StatusBadRequest, map[string]any{"error": err.Error()})
				return
			}
			req.SessionID = parts[0]
			req.Op = parts[1]
		} else {
			writeJSON(w, http.StatusNotFound, map[string]any{"error": "route not found"})
			return
		}
	default:
		writeJSON(w, http.StatusNotFound, map[string]any{"error": "route not found"})
		return
	}
	err := s.worker.Do(r.Context(), func() error { var err error; result, err = s.dispatch(req, r.Context()); return err })
	if err == nil && r.Context().Err() != nil {
		err = r.Context().Err()
	}
	if err != nil {
		status := http.StatusInternalServerError
		var ae *apiError
		if errors.As(err, &ae) {
			status = ae.status
		} else if errors.Is(err, context.Canceled) {
			status = 499
		}
		// A recoverable native failure can also leave a partial write. Invalidate that session.
		if (status >= 500 || status == 499) && requestSessionID() != "" {
			_ = s.worker.Do(context.Background(), func() error { s.closeSession(requestSessionID()); return nil })
		}
		writeJSON(w, status, map[string]any{"error": err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, result)
}

func main() {
	address := flag.String("listen", "127.0.0.1:11551", "loopback address")
	modelName := flag.String("model", "", "existing local Ollama alias; no download occurs")
	expectedManifest := flag.String("expected-manifest", canonicalManifest, "required local manifest SHA256; empty permits another explicit candidate")
	maxContext := flag.Int("max-context", 4096, "maximum committed plus verified token positions")
	maxDraft := flag.Int("max-draft", 16, "maximum proposed block length")
	maxSessions := flag.Int("max-sessions", 1, "maximum simultaneous session caches")
	prefillChunk := flag.Int("prefill-chunk", 512, "prefill forward chunk size")
	probe := flag.Bool("probe", false, "verify runtime and manifest metadata without loading model tensors")
	flag.Parse()
	if *modelName == "" {
		if *probe {
			*modelName = canonicalModel
		} else {
			log.Fatal("--model is required; use --probe for metadata without loading weights")
		}
	}
	host, _, err := net.SplitHostPort(*address)
	if err != nil || (host != "127.0.0.1" && host != "::1" && host != "localhost") {
		log.Fatal("listen must specify a loopback host and port")
	}
	if *maxContext < 2 || *maxDraft < 0 || *maxDraft > 64 || *maxSessions < 1 || *prefillChunk < 1 {
		log.Fatal("invalid context/draft/session/chunk limit")
	}
	m, err := manifest.ParseNamedManifest(modeltypes.ParseName(*modelName))
	if err != nil {
		log.Fatal(err)
	}
	digest := strings.TrimPrefix(m.Digest(), "sha256:")
	if *expectedManifest != "" && digest != strings.TrimPrefix(*expectedManifest, "sha256:") {
		log.Fatalf("manifest changed: got %s expected %s", digest, *expectedManifest)
	}
	fingerprint, special, err := tokenizerMetadata(m)
	if err != nil {
		log.Fatal(err)
	}
	tokenizerLayer, ok := m.ConfigLayer("tokenizer.json")
	if !ok {
		log.Fatal("model manifest has no tokenizer.json")
	}
	worker, err := mlxthread.Start("speculative-target", func() error {
		if err := mlx.CheckInit(); err != nil {
			return err
		}
		if !mlx.MetalIsAvailable() {
			return errors.New("Apple Metal GPU is unavailable")
		}
		mlx.SetDefaultDeviceGPU()
		return nil
	})
	if err != nil {
		log.Fatal(err)
	}
	library, err := mlx.LoadedLibraryPath()
	if err != nil {
		log.Fatal(err)
	}
	if *probe {
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"model": *modelName, "manifest_sha256": digest, "tokenizer_sha256": strings.TrimPrefix(tokenizerLayer.Digest, "sha256:"), "source_revision": sourceRevision, "mlx_library": library, "mlx_version": mlx.Version(), "mlx_c_source_revision": mlxCSourceRevision, "model_loaded": false, "tokenizer_fingerprint": fingerprint, "special_token_ids": special})
		_ = worker.Stop(context.Background(), nil)
		return
	}
	runner := &mlxrunner.Runner{}
	if err := worker.Do(context.Background(), func() error { return runner.Load(*modelName) }); err != nil {
		log.Fatal(err)
	}
	svc := &service{runner: runner, worker: worker, model: *modelName, manifest: digest, tokenizer: strings.TrimPrefix(tokenizerLayer.Digest, "sha256:"), fingerprint: fingerprint, special: special, maxContext: min(*maxContext, runner.Model.MaxContextLength()), maxDraft: *maxDraft, maxSessions: *maxSessions, prefillChunk: *prefillChunk, sessions: make(map[string]*session), library: library}
	listener, err := net.Listen("tcp", *address)
	if err != nil {
		_ = worker.Stop(context.Background(), svc.shutdown)
		log.Fatal(err)
	}
	server := &http.Server{Handler: svc, ReadHeaderTimeout: 5 * time.Second, IdleTimeout: 30 * time.Second}
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()
	go func() {
		<-ctx.Done()
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		_ = server.Shutdown(shutdownCtx)
	}()
	log.Printf("native greedy verifier on %s; exact model %s; manifest %s", listener.Addr(), *modelName, digest)
	if err := server.Serve(listener); err != nil && !errors.Is(err, http.ErrServerClosed) {
		log.Print(err)
	}
	_ = worker.Stop(context.Background(), svc.shutdown)
}
