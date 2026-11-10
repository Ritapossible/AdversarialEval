// stage1check runs the kit's own Stage 1 package checks (adapterbuild.CheckLoRA, unmodified)
// with the intent class taken from the live node instead of the kit's offline catalog.
//
// Why: the kit's compiled-in catalog does not distinguish judgment from hybrid and reports
// "hybrid" when unsure (pkg/scoring/catalog.ClassOf), so offline `adapterbuild lora` demands
// hybrid for SECURITY_REVIEW while the live node classifies it as judgment and rejects hybrid
// packages with class_mismatch (as happened to registration #62 on EMAIL_SECURITY).
//
//	go run . --intent SECURITY_REVIEW --package <pkg> --foundation <foundation.json> [--out dir]
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/telegraphprotocol/telegraph-wasm-baseline/pkg/adapterbuild"
	"github.com/telegraphprotocol/telegraph-wasm-baseline/pkg/scoring/catalog"
)

func liveClass(node, intent string) (string, error) {
	c := &http.Client{Timeout: 30 * time.Second}
	resp, err := c.Get(node + "/engine/v1/intents/" + intent)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return "", fmt.Errorf("node returned %s for intent %s", resp.Status, intent)
	}
	var v struct {
		Class string `json:"class"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&v); err != nil {
		return "", err
	}
	if v.Class != "judgment" && v.Class != "hybrid" {
		return "", fmt.Errorf("node classifies %s as %q, which takes no float adapter", intent, v.Class)
	}
	return v.Class, nil
}

func main() {
	intent := flag.String("intent", "", "family prefix the package serves (required)")
	pkg := flag.String("package", "", "safetensors delta package (required)")
	foundation := flag.String("foundation", "", "foundation.json (required)")
	out := flag.String("out", "", "manifest directory (default: next to the package)")
	node := flag.String("node", "https://devnode.telegraphprotocol.com", "node to read the intent class from")
	class := flag.String("class", "", "skip the node lookup and use this class (judgment|hybrid)")
	flag.Parse()
	fail := func(err error) { fmt.Fprintf(os.Stderr, "stage1check: FAILED: %v\n", err); os.Exit(1) }
	if *intent == "" || *pkg == "" || *foundation == "" {
		fail(fmt.Errorf("--intent, --package and --foundation are required"))
	}
	cls, source := *class, "--class"
	if cls == "" {
		var err error
		if cls, err = liveClass(*node, *intent); err != nil {
			fail(err)
		}
		source = *node
	}
	catalog.UseClasses(map[string]catalog.Class{*intent: catalog.Class(cls)})
	logf := func(format string, a ...any) { fmt.Fprintf(os.Stderr, "stage1check: "+format+"\n", a...) }
	logf("class %s for %s (from %s)", cls, *intent, source)
	art, man, err := adapterbuild.CheckLoRA(context.Background(), adapterbuild.LoRAReq{
		Intent: *intent, PackagePath: *pkg, Class: cls, FoundationPath: *foundation, OutDir: *out,
	}, logf)
	if err != nil {
		fail(err)
	}
	b, _ := json.Marshal(map[string]any{
		"intent": *intent, "class": man.Class, "class_source": source, "keccak256": art.Keccak256,
		"sha256": art.SHA256, "bytes": art.Bytes, "package_path": art.Path, "manifest_path": art.ManifestPath,
	})
	fmt.Println(string(b))
}
