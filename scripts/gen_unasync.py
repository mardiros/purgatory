from pathlib import Path

import unasync

unasync.unasync_files(
    [str(p) for p in Path("src/purgatory/service/_async").iterdir() if p.is_file()],
    rules=[
        unasync.Rule(
            "src/purgatory/service/_async",
            "src/purgatory/service/_sync",
            additional_replacements={
                "aioredis": "redis",
                "_async": "_sync",
            },
        ),
    ],
)

unasync.unasync_files(
    [str(p) for p in Path("tests/unittests/_async").iterdir() if p.is_file()],
    rules=[
        unasync.Rule(
            "tests/unittests/_async",
            "tests/unittests/_sync",
            additional_replacements={
                "aioredis": "redis",
                "_async": "_sync",
                "AsyncSleep": "SyncSleep",
            },
        ),
    ],
)
