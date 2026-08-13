# app/content/load.py
"""
python -m app.content.load

Upserts content/exercises/*.md and content/routines/*.yaml into Postgres.
Safe to re-run: exercises are updated in place by slug; each routine's
block/exercise structure is rebuilt from the content file on every run so
the nested structure can't drift out of sync with what's on disk.
"""
import asyncio
import sys
from pathlib import Path

import frontmatter
import yaml
from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import create_engine_from_url, create_session_factory
from app.content.markdown import parse_sections
from app.content.schemas import ExerciseFrontmatter, RoutineFile
from app.models.library import BlockExercise, BlockKind, LibraryExercise, Routine, RoutineBlock

CONTENT_DIR = Path(__file__).resolve().parent.parent.parent / "content"
EXERCISES_DIR = CONTENT_DIR / "exercises"
ROUTINES_DIR = CONTENT_DIR / "routines"

ExerciseRecord = tuple[Path, ExerciseFrontmatter, str, str]
RoutineRecord = tuple[Path, RoutineFile]


class ContentError(Exception):
    pass


def load_exercise_files() -> list[ExerciseRecord]:
    errors: list[str] = []
    results: list[ExerciseRecord] = []

    for path in sorted(EXERCISES_DIR.glob("*.md")):
        post = frontmatter.load(path)
        try:
            data = ExerciseFrontmatter(**post.metadata)
        except ValidationError as e:
            errors.append(f"{path.name}: {e}")
            continue

        if data.slug != path.stem:
            errors.append(f"{path.name}: frontmatter slug {data.slug!r} does not match filename")

        sections = parse_sections(post.content)
        setup = sections.get("setup", "")
        execution = sections.get("execution", "")
        if not setup:
            errors.append(f"{path.name}: missing '## Setup' section")
        if not execution:
            errors.append(f"{path.name}: missing '## Execution' section")

        results.append((path, data, setup, execution))

    if errors:
        raise ContentError("Exercise content errors:\n" + "\n".join(f"  - {e}" for e in errors))
    return results


def load_routine_files() -> list[RoutineRecord]:
    errors: list[str] = []
    results: list[RoutineRecord] = []

    for path in sorted(ROUTINES_DIR.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text())
        try:
            data = RoutineFile(**raw)
        except ValidationError as e:
            errors.append(f"{path.name}: {e}")
            continue

        if data.slug != path.stem:
            errors.append(f"{path.name}: slug {data.slug!r} does not match filename")

        results.append((path, data))

    if errors:
        raise ContentError("Routine content errors:\n" + "\n".join(f"  - {e}" for e in errors))
    return results


def check_exercise_refs(exercises: list[ExerciseRecord], routines: list[RoutineRecord]) -> None:
    known = {data.slug for _, data, _, _ in exercises}
    errors: list[str] = []

    for path, routine in routines:
        for block in routine.blocks:
            for item in block.exercises:
                if item.exercise not in known:
                    errors.append(
                        f"{path.name}: routine {routine.slug!r} references unknown exercise slug {item.exercise!r}"
                    )

    if errors:
        raise ContentError("Routine reference errors:\n" + "\n".join(f"  - {e}" for e in errors))


async def upsert_exercises(db: AsyncSession, exercises: list[ExerciseRecord]) -> dict[str, int]:
    slug_to_id: dict[str, int] = {}

    for _, data, setup, execution in exercises:
        result = await db.execute(select(LibraryExercise).where(LibraryExercise.slug == data.slug))
        row = result.scalar_one_or_none()

        fields = dict(
            name=data.name,
            aliases=data.aliases,
            primary_muscle=data.primary_muscle,
            secondary_muscles=data.secondary_muscles,
            equipment=data.equipment,
            category=data.category,
            setup=setup,
            execution=execution,
            cues=data.cues,
            common_faults=data.common_faults,
            video_url=data.video_url,
            thumbnail_url=data.thumbnail_url,
        )

        if row is None:
            row = LibraryExercise(slug=data.slug, **fields)
            db.add(row)
        else:
            for key, value in fields.items():
                setattr(row, key, value)

        await db.flush()
        slug_to_id[data.slug] = row.id

    return slug_to_id


async def upsert_routines(
    db: AsyncSession, routines: list[RoutineRecord], slug_to_id: dict[str, int]
) -> None:
    # Every row here is created/deleted through explicit FK ids and db.add(),
    # never through relationship-collection mutation (.blocks.append(), etc).
    # AsyncSession can't service an implicit lazy load triggered by plain
    # attribute access outside an awaited call, and touching a relationship
    # collection after a flush is exactly what triggers one.
    for _, data in routines:
        result = await db.execute(select(Routine).where(Routine.slug == data.slug))
        routine = result.scalar_one_or_none()

        if routine is None:
            routine = Routine(slug=data.slug)
            db.add(routine)

        routine.name = data.name
        routine.description = data.description
        routine.goal = data.goal
        routine.day_label = data.day_label
        routine.estimated_minutes = data.estimated_minutes
        await db.flush()  # ensures routine.id is set for a brand-new routine

        # Rebuild the block structure from scratch each run rather than
        # diffing it — old rows must be physically deleted (flushed) before
        # new rows reuse the same (routine_id, order) values, since a single
        # flush applies inserts before deletes for rows of the same table.
        old_block_ids = (
            await db.execute(select(RoutineBlock.id).where(RoutineBlock.routine_id == routine.id))
        ).scalars().all()
        if old_block_ids:
            await db.execute(delete(BlockExercise).where(BlockExercise.block_id.in_(old_block_ids)))
            await db.execute(delete(RoutineBlock).where(RoutineBlock.id.in_(old_block_ids)))
            await db.flush()

        for block_order, block_data in enumerate(data.blocks, start=1):
            block = RoutineBlock(
                routine_id=routine.id,
                order=block_order,
                kind=BlockKind(block_data.kind),
                rounds=block_data.rounds,
                rest_after_seconds=block_data.rest_after_seconds,
                notes=block_data.notes,
            )
            db.add(block)
            await db.flush()  # need block.id for the child rows below

            for ex_order, item in enumerate(block_data.exercises, start=1):
                db.add(
                    BlockExercise(
                        block_id=block.id,
                        order=ex_order,
                        exercise_id=slug_to_id[item.exercise],
                        sets=item.sets,
                        reps=item.reps,
                        load_note=item.load_note,
                        tempo=item.tempo,
                        rest_seconds=item.rest_seconds,
                        notes=item.notes,
                    )
                )
        await db.flush()


async def main() -> None:
    exercises = load_exercise_files()
    routines = load_routine_files()
    check_exercise_refs(exercises, routines)

    settings = get_settings()
    engine = create_engine_from_url(settings.database_url)
    session_factory = create_session_factory(engine)

    async with session_factory() as db:
        slug_to_id = await upsert_exercises(db, exercises)
        await upsert_routines(db, routines, slug_to_id)
        await db.commit()

    await engine.dispose()
    print(f"Loaded {len(exercises)} exercises and {len(routines)} routines.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ContentError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
