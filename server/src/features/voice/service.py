"""Temporary, local macOS speech provider. No external service or API key."""

import asyncio
from pathlib import Path
import sys
import tempfile

from fastapi import HTTPException


# One bounded synthesis job per process. Reject excess work rather than building
# an unbounded queue behind the model on a developer's machine.
_synthesis_lock = asyncio.Lock()


async def synthesize(text: str) -> bytes:
    if sys.platform != "darwin":
        raise HTTPException(503, "AI voice currently needs the Mula backend to run on macOS. Chat still works.")
    if _synthesis_lock.locked():
        raise HTTPException(429, "Voice is busy. Try playing the reply again in a moment.")

    async with _synthesis_lock:
        with tempfile.TemporaryDirectory(prefix="mula-speech-") as directory:
            source = Path(directory) / "input.txt"
            output = Path(directory) / "speech.wav"
            # A private input file avoids putting conversation text in process
            # arguments. No shell is used and client text cannot supply flags.
            source.write_text(text, encoding="utf-8")
            process = None
            try:
                process = await asyncio.create_subprocess_exec(
                    "/usr/bin/say", "-f", str(source), "-o", str(output),
                    "--file-format=WAVE", "--data-format=LEI16@22050",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await asyncio.wait_for(process.wait(), timeout=30)
                if process.returncode != 0 or not output.exists():
                    raise HTTPException(503, "Could not create AI voice. Check the Mac's installed speech voice.")
                audio = output.read_bytes()
                if len(audio) < 44 or audio[:4] != b"RIFF" or len(audio) > 16_000_000:
                    raise HTTPException(503, "The speech engine returned invalid audio. Chat still works.")
                return audio
            except TimeoutError as error:
                raise HTTPException(504, "Voice generation took too long. Try a shorter reply.") from error
            except OSError as error:
                raise HTTPException(503, "The local speech engine is unavailable. Chat still works.") from error
            finally:
                # Also runs on cancellation; never leave synthesis running after
                # its request is cancelled or its temporary directory is removed.
                if process is not None and process.returncode is None:
                    process.kill()
                    await process.wait()
