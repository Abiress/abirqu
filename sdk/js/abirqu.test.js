import test from "node:test";
import assert from "node:assert/strict";
import { version } from "./abirqu.js";

test("version returns non-empty string", () => {
  assert.ok(version().length > 0);
});
