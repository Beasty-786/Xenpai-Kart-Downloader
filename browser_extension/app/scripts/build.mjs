import {access, cp, mkdir, readdir, readFile, rm, writeFile} from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";

import {build as esbuild} from "esbuild";
import {build as viteBuild} from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(__dirname, "..");
const upstreamDir = path.resolve(appRoot, "../upstream");
const catchScriptDir = path.resolve(upstreamDir, "catch-script");
const upstreamContentScript = path.resolve(upstreamDir, "js/content-script.js");
const firefoxAddonId = "xenpai-kart-downloader@beasty-786.github.io";
const manifestTemplate = JSON.parse(
  await readFile(path.resolve(appRoot, "public/manifest.json"), "utf8"),
);

const buildTargets = {
  chromium: {
    outDir: path.resolve(appRoot, "../chromium"),
    runtimeTarget: "chrome114",
  },
  firefox: {
    outDir: path.resolve(appRoot, "../firefox"),
    runtimeTarget: "firefox113",
  },
};

function createManifest(target) {
  const manifest = structuredClone(manifestTemplate);

  if (target === "firefox") {
    manifest.background = {
      scripts: ["background.js"],
      type: "module",
    };
    manifest.browser_specific_settings = {
      gecko: {
        id: firefoxAddonId,
        strict_min_version: "113.0",
        data_collection_permissions: {
          required: ["browsingActivity", "websiteContent"],
        },
      },
    };
    delete manifest.minimum_chrome_version;
    delete manifest.side_panel;
    manifest.permissions = manifest.permissions.filter(p => p !== "sidePanel");
    return manifest;
  }

  manifest.background = {
    service_worker: "background.js",
    type: "module",
  };
  manifest.minimum_chrome_version = "114";
  delete manifest.browser_specific_settings;
  return manifest;
}

try {
  await access(catchScriptDir);
  await access(upstreamContentScript);
} catch {
  throw new Error(
    "Missing browser_extension/upstream files. Run `git submodule update --init --recursive browser_extension/upstream` first.",
  );
}

for (const [target, config] of Object.entries(buildTargets)) {
  process.env.GD4B_BROWSER_TARGET = target;

  await viteBuild({
    configFile: path.resolve(appRoot, "vite.config.ts"),
    mode: "production",
    build: {
      outDir: config.outDir,
      emptyOutDir: true,
      target: config.runtimeTarget,
    },
  });

  await esbuild({
    entryPoints: [path.resolve(appRoot, "src/background.ts")],
    bundle: true,
    format: "esm",
    target: config.runtimeTarget,
    platform: "browser",
    outfile: path.resolve(config.outDir, "background.js"),
  });

  await esbuild({
    entryPoints: [path.resolve(appRoot, "src/content-script.ts")],
    bundle: true,
    format: "iife",
    target: config.runtimeTarget,
    platform: "browser",
    outfile: path.resolve(config.outDir, "content-script.js"),
  });

  // GD3's own page-media probe (MAIN world) and download button (ISOLATED world). Authored
  // in TS under src/page-media — kept out of the vendored catch-script/ directory on purpose.
  await esbuild({
    entryPoints: [path.resolve(appRoot, "src/page-media/attribution/mse-probe.ts")],
    bundle: true,
    format: "iife",
    target: config.runtimeTarget,
    platform: "browser",
    outfile: path.resolve(config.outDir, "page-media-probe.js"),
  });

  await esbuild({
    entryPoints: [path.resolve(appRoot, "src/page-media/download-button/download-button.ts")],
    bundle: true,
    format: "iife",
    target: config.runtimeTarget,
    platform: "browser",
    outfile: path.resolve(config.outDir, "page-media-overlay.js"),
  });

  await mkdir(config.outDir, { recursive: true });
  await cp(catchScriptDir, path.resolve(config.outDir, "catch-script"), { recursive: true });
  await cp(upstreamContentScript, path.resolve(config.outDir, "cat-catch-content-script.js"));
  await writeFile(
    path.resolve(config.outDir, "manifest.json"),
    `${JSON.stringify(createManifest(target), null, 2)}\n`,
  );

  // Xenpai is distributed as an English-only extension. Vite copies every
  // source locale from public/, so remove all but en_US from the artifact.
  const localeDir = path.resolve(config.outDir, "_locales");
  for (const locale of await readdir(localeDir)) {
    if (locale !== "en_US") {
      await rm(path.resolve(localeDir, locale), { recursive: true, force: true });
    }
  }
}

delete process.env.GD4B_BROWSER_TARGET;
