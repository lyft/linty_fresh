import asyncio
import json
import tempfile

from linty_fresh.problem import Problem

from typing import Set


MAX_REVISIONS = 10
NOTES_REF = 'refs/notes/linty_fresh'
GIT_SUBPROCESS_KWARGS = {
    'stdout': asyncio.subprocess.PIPE,
    'stderr': asyncio.subprocess.DEVNULL,
    'env': {
        'GIT_NOTES_REF': NOTES_REF
    }
}


class GitNotesStorageEngine(object):
    def __init__(self, remote: str=None):
        self.remote = remote

    async def get_existing_problems(self) -> Set[Problem]:
        note_ref = ''
        result = set()
        if self.remote:
            fetch_notes = await asyncio.create_subprocess_exec(
                'git', 'fetch', self.remote, '{0}:{0}'.format(NOTES_REF),
                **GIT_SUBPROCESS_KWARGS)
            await fetch_notes.wait()

        last_n_revisions_proc = await asyncio.create_subprocess_exec(
            'git', 'log', '--skip=1', '-{}'.format(MAX_REVISIONS),
            '--pretty=%H',
            **GIT_SUBPROCESS_KWARGS)
        async for line in last_n_revisions_proc.stdout:
            notes_ref_proc = await asyncio.create_subprocess_exec(
                'git', 'notes', 'list', line.decode().strip(),
                **GIT_SUBPROCESS_KWARGS)
            await notes_ref_proc.wait()
            if notes_ref_proc.returncode == 0:
                note_ref = (
                    await notes_ref_proc.stdout.readline()).decode().strip()
                if note_ref:
                    break
        await last_n_revisions_proc.wait()
        if note_ref:
            notes_proc = await asyncio.create_subprocess_exec(
                'git', 'show', note_ref,
                **GIT_SUBPROCESS_KWARGS)
            async for line in notes_proc.stdout:
                try:
                    problems = json.loads(line.decode())
                    for problem in problems:
                        result.add(Problem.from_json(problem))
                except Exception:
                    pass
            await notes_proc.wait()
        return result

    async def store_problems(self, problems: Set[Problem]) -> None:
        with tempfile.NamedTemporaryFile() as problem_file:
            result = sorted([problem.to_json() for problem in problems],
                            key=lambda x: str(x))
            problem_file.write(json.dumps(result).encode())
            problem_file.flush()
            notes_proc = await asyncio.create_subprocess_exec(
                'git', 'notes', 'append', '-F', problem_file.name,
                **GIT_SUBPROCESS_KWARGS)
            await notes_proc.wait()
            if self.remote:
                push_proc = await asyncio.create_subprocess_exec(
                    'git', 'push', '-f', '-q', self.remote, NOTES_REF,
                    **GIT_SUBPROCESS_KWARGS)
                await push_proc.wait()
