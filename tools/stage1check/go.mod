module github.com/ritapossible/adversarialeval/tools/stage1check

go 1.25.7

require github.com/telegraphprotocol/telegraph-wasm-baseline v0.0.0

require (
	github.com/ProjectZKM/Ziren/crates/go-runtime/zkvm_runtime v0.0.0-20251001021608-1fe7b43fc4d6 // indirect
	github.com/decred/dcrd/dcrec/secp256k1/v4 v4.4.0 // indirect
	github.com/ethereum/go-ethereum v1.16.7 // indirect
	github.com/holiman/uint256 v1.3.2 // indirect
	github.com/mattn/go-colorable v0.1.14 // indirect
	github.com/mattn/go-isatty v0.0.20 // indirect
	github.com/rs/zerolog v1.35.1 // indirect
	github.com/tetratelabs/wazero v1.12.0 // indirect
	golang.org/x/crypto v0.48.0 // indirect
	golang.org/x/sys v0.44.0 // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)

replace github.com/telegraphprotocol/telegraph-wasm-baseline => ../../third_party/telegraph-wasm-baseline
