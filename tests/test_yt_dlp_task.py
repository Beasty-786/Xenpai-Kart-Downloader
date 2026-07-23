import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "features"))

from ffmpeg_pack.task import FFmpegResourceStep, FFmpegStep
from yt_dlp_pack.task import YouTubeMergeStep, YouTubeResourceStep


@pytest.mark.asyncio
async def test_youtube_resource_forwards_speed_callbacks(monkeypatch):
    received = {}

    async def parent_run(self, report_speed, wait_for_speed_limit):
        received["report_speed"] = report_speed
        received["wait_for_speed_limit"] = wait_for_speed_limit

    monkeypatch.setattr(FFmpegResourceStep, "run", parent_run)

    step = YouTubeResourceStep(stepIndex=0, url="https://example.test/video")
    report_speed = object()
    wait_for_speed_limit = object()

    await step.run(report_speed, wait_for_speed_limit)

    assert received == {
        "report_speed": report_speed,
        "wait_for_speed_limit": wait_for_speed_limit,
    }


@pytest.mark.asyncio
async def test_youtube_merge_forwards_speed_callbacks(monkeypatch, tmp_path: Path):
    received = {}

    async def parent_run(self, report_speed, wait_for_speed_limit):
        received["report_speed"] = report_speed
        received["wait_for_speed_limit"] = wait_for_speed_limit

    monkeypatch.setattr(FFmpegStep, "run", parent_run)

    step = YouTubeMergeStep(
        stepIndex=0,
        videoStem="sample",
        videoExtension="mp4",
        audioExtension="m4a",
    )
    step._task = SimpleNamespace(name="sample.mp4", outputFolder=tmp_path)
    step._videoPath.touch()
    step._audioPath.touch()
    report_speed = object()
    wait_for_speed_limit = object()

    await step.run(report_speed, wait_for_speed_limit)

    assert received == {
        "report_speed": report_speed,
        "wait_for_speed_limit": wait_for_speed_limit,
    }
