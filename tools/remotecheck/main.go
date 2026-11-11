// Command remotecheck rehearses the Telegraph node's remote check against a local
// executor, using the node's own client code (pkg/wasm/remote, vendored in the kit).
//
// It sends preference pairs in batches of 15 (30 texts, as the node does) with the score
// identity, rejects a different echo exactly as the node would, and reports how many pairs
// the executor orders correctly. It also writes every score so it can be compared with the
// PyTorch path (eval/score.py).
//
//	WASM_REMOTE_ALLOW_PRIVATE=true remotecheck --url http://127.0.0.1:8088 \
//	    --batch runs/rehearsal/batch.json --adapter-hash 0x... --out runs/rehearsal/wasm_scores.json
//
// WASM_REMOTE_ALLOW_PRIVATE is the client's documented local-test switch; real validators
// never set it, so a public executor must still be reachable over HTTPS.
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/telegraphprotocol/telegraph-wasm-baseline/pkg/wasm/remote"
)

type pair struct {
	RowID    string  `json:"row_id"`
	Chosen   []int64 `json:"chosen"`
	Rejected []int64 `json:"rejected"`
}

type result struct {
	RowID    string  `json:"row_id"`
	Chosen   float32 `json:"chosen"`
	Rejected float32 `json:"rejected"`
	Correct  float64 `json:"correct"`
}

func main() {
	url := flag.String("url", "http://127.0.0.1:8088", "executor URL")
	batchPath := flag.String("batch", "", "batch.json from tools/rehearse_batch.py")
	foundation := flag.String("foundation-json", "third_party/foundation/foundation.json", "foundation.json")
	adapterHash := flag.String("adapter-hash", "", "keccak256 of the package (0x optional)")
	per := flag.Int("per-request", 15, "pairs per request (the node sends 15)")
	out := flag.String("out", "", "write per-pair scores here")
	flag.Parse()

	var f struct {
		FoundationHash string `json:"foundation_hash"`
		TokenizerHash  string `json:"tokenizer_hash"`
	}
	must(readJSON(*foundation, &f))
	var b struct {
		Pairs []pair `json:"pairs"`
	}
	must(readJSON(*batchPath, &b))
	ident := &remote.BatchIdentity{
		FoundationHash: f.FoundationHash,
		AdapterHash:    strings.TrimPrefix(strings.ToLower(*adapterHash), "0x"),
		TokenizerHash:  f.TokenizerHash,
	}
	ex := remote.NewRemoteExecutor(*url)
	var res []result
	var correct float64
	for start := 0; start < len(b.Pairs); start += *per {
		end := min(start+*per, len(b.Pairs))
		var toks [][]int64
		for _, p := range b.Pairs[start:end] {
			toks = append(toks, p.Chosen, p.Rejected)
		}
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Minute)
		t0 := time.Now()
		scores, echoed, err := ex.ScoreBatchWithIdentity(ctx, toks, ident)
		cancel()
		if err != nil {
			fmt.Fprintf(os.Stderr, "REJECT (as the node would): %v\n", err)
			os.Exit(1)
		}
		if !echoed {
			fmt.Fprintln(os.Stderr, "REJECT (as the node would): the executor did not echo the score identity")
			os.Exit(1)
		}
		var chunk float64
		for i, p := range b.Pairs[start:end] {
			c, r := scores[2*i], scores[2*i+1]
			if c.Error != "" || r.Error != "" {
				fmt.Fprintf(os.Stderr, "REJECT (as the node would): refused pair %s: %s%s\n", p.RowID, c.Error, r.Error)
				os.Exit(1)
			}
			cs, rs := c.Score.Float32(), r.Score.Float32()
			ok := 0.0
			if cs > rs {
				ok = 1
			} else if cs == rs {
				ok = 0.5
			}
			chunk += ok
			res = append(res, result{p.RowID, cs, rs, ok})
		}
		correct += chunk
		n := end - start
		verdict := "pass"
		if chunk/float64(n) < 0.70 {
			verdict = "FAIL (<70%)"
		}
		fmt.Printf("request %d: pairs %d-%d, identity echoed, %.1f/%d correct (%.1f%%) %s, %s\n",
			start / *per + 1, start+1, end, chunk, n, 100*chunk/float64(n), verdict, time.Since(t0).Round(time.Second))
	}
	fmt.Printf("total: %.1f/%d pairs ordered correctly (%.1f%%)\n", correct, len(b.Pairs), 100*correct/float64(len(b.Pairs)))
	if *out != "" {
		data, _ := json.MarshalIndent(res, "", " ")
		must(os.WriteFile(*out, append(data, '\n'), 0o644))
	}
}

func readJSON(path string, v any) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, v)
}

func must(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
}
