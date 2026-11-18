# Version adapters / 版本适配

The current adapter separates player UI, HLS selection and worker buffering into three modules:

- `atvpatch/adapters/apple_tv_14_3_1.json`: package/version, original hashes, transformations.
- `atvpatch/adapters/v14_3_1/player.py`: player UI and controls.
- `atvpatch/adapters/v14_3_1/hls.py`: quality and bounded prefetch.
- `atvpatch/adapters/v14_3_1/worker.py`: buffer metrics and memory policy.
- `atvpatch/patches.py`: validation and composition.
- `atvpatch/profiles/*.json`: explicit device policy; no automatic device inference.

For a new version, add a distinct module and manifest, retaining the old validation path. Record hashes from locally obtained original inputs; review every anchor and require uniqueness. Do not commit vendor code or APKs. Add synthetic transformation and rejection tests. The current CLI selects only the registered 14.3.1 adapter; another version also needs explicit selection logic and ambiguity tests. Copying a JSON file alone does not register an adapter.

Physical checks must cover login, the same title/track, HDR/audio, subtitles/episodes, long-press, paused downloads, memory and rollback. Start with a one-minute test and record each device independently.
