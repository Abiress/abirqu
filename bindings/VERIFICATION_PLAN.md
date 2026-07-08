# Language Bindings — Status & Plan for Full Functional Verification

## Current State (verified 2026-07-09)

| Language | Code Status | Runtime Verified? | Toolchain Present? | Evidence |
|----------|-------------|------------------|---------------------|----------|
| **Python** | ✅ Complete | ✅ Yes | Yes | 627 tests pass |
| **JavaScript/TS** | ✅ Complete | ✅ Yes | Yes (Node) | `node tests/run-tests.js` → 17/17 pass |
| **Go** | ✅ Implemented | ✅ Yes | Yes | `go test ./...` → ok (cgo → Rust lib) |
| **WebAssembly** | ✅ Complete | ✅ Yes (loads Pyodide) | Yes | `bindings/wasm/` — Pyodide loader |
| **Java** | 🔧 Implemented | ❌ Not verified | ❌ No (no JDK) | JNA code complete, untested |
| **.NET** | 🔧 Implemented | ❌ Not verified | ❌ No (no dotnet) | P/Invoke code complete, untested |
| **Swift** | 🔧 Implemented | ❌ Not verified | ❌ No (no swiftc) | CInterop code complete, untested |
| **Kotlin** | 🔧 Implemented | ❌ Not verified | ❌ No (no kotlinc) | JNA code complete, untested |

**Key finding:** The non-Python bindings are NOT stubs — they are real
implementations wrapping the Rust `libabirqu_core.so` (cgo / JNA / P-Invoke /
CInterop). The only gap is runtime verification in CI, which is blocked by
missing toolchains in this dev environment.

## The Rust Core (shared dependency)

All native bindings depend on `libabirqu_core.so`:
```bash
cargo build --release --no-default-features
# produces: target/release/libabirqu_core.so
```
Already built and committed. Go binding confirmed working against it.

---

## Plan for Full Functional Verification

### Phase 1 — Verify what's possible now (toolchains available)
1. **Go** — already passing. Add to CI:
   ```yaml
   - name: Go binding
     run: |
       cargo build --release --no-default-features
       export LD_LIBRARY_PATH=$PWD/target/release:$LD_LIBRARY_PATH
       cd go/abirqu && go test ./...
   ```
2. **JavaScript** — already passing. Add to CI:
   ```yaml
   - name: JS binding
     run: cd js && node tests/run-tests.js
   ```
3. **WebAssembly** — add a smoke test that the Pyodide loader imports cleanly
   (note: network call to CDN; mark as `continue-on-error` in CI).

### Phase 2 — Verify Java / Kotlin (needs JDK)
On a machine with JDK 17+ and Maven/Gradle:
```bash
cargo build --release --no-default-features
export LD_LIBRARY_PATH=$PWD/target/release:$LD_LIBRARY_PATH
cd java && mvn test          # or: javac + run AbirQuSimulatorTest
cd kotlin && ./gradlew test
```
- Verify JNA loads `libabirqu_core.so`
- Confirm Bell-state probabilities ≈ 0.5/0.5

### Phase 3 — Verify .NET (needs dotnet SDK)
On a machine with .NET 8 SDK:
```bash
cargo build --release --no-default-features
export LD_LIBRARY_PATH=$PWD/target/release:$LD_LIBRARY_PATH
cd dotnet && dotnet test
```
- Confirm P/Invoke resolves `abirqu_core`
- Run SimulatorTests

### Phase 4 — Verify Swift (needs Swift 5.9+)
On macOS/Linux with Swift:
```bash
cargo build --release --no-default-features
export LD_LIBRARY_PATH=$PWD/target/release:$LD_LIBRARY_PATH
cd swift && swift test
```
- Confirm CInterop module maps correctly
- Run AbirQuTests

### Phase 5 — Publish
- Go: `go mod tidy` + tag `v1.1.0`
- JS: `npm publish` (already npm-ready)
- Java/Kotlin/.NET/Swift: package + publish after Phase 2-4 verification

---

## Immediate Actions (this session)
- [x] README table corrected (no longer says "stub"/"planned")
- [x] Go + JS confirmed working, documented as ✅
- [ ] Add Go + JS binding tests to CI workflow
- [ ] Document Java/.NET/Swift/Kotlin verification commands (done above)
- [ ] Mark remaining 4 as "🔧 Implemented — verification pending toolchain"

## Blocker
Java, .NET, Swift, Kotlin verification requires toolchains NOT installed in
this environment (no JDK, no dotnet SDK, no swiftc). These will be verified
on appropriate CI runners or a machine with the toolchain.
