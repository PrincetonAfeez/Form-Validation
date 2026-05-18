import { copyFileSync, mkdirSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const vendorDir = join(root, "static", "js", "vendor");

mkdirSync(vendorDir, { recursive: true });

const copies = [
  ["node_modules/htmx.org/dist/htmx.min.js", "htmx.min.js"],
  ["node_modules/alpinejs/dist/cdn.min.js", "alpine.min.js"],
];

for (const [from, to] of copies) {
  copyFileSync(join(root, from), join(vendorDir, to));
}
