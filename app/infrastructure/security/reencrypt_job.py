from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.infrastructure.security.field_encryption import decrypt_text, encrypt_text
from app.infrastructure.settings import get_settings


@dataclass(slots=True)
class FieldTarget:
    table: str
    field: str


TARGET_FIELDS: tuple[FieldTarget, ...] = (
    FieldTarget(table="patient", field="medical_history"),
    FieldTarget(table="patient", field="notes"),
    FieldTarget(table="consultation", field="diagnosis"),
    FieldTarget(table="consultation", field="notes"),
    FieldTarget(table="consultation", field="chief_complaint"),
    FieldTarget(table="consultation", field="physical_exam"),
    FieldTarget(table="consultation", field="conduct"),
    FieldTarget(table="patient_continuous_medication", field="name"),
    FieldTarget(table="patient_continuous_medication", field="dosage"),
    FieldTarget(table="patient_continuous_medication", field="notes"),
    FieldTarget(table="patient_medical_history", field="body"),
    FieldTarget(table="exam", field="name"),
    FieldTarget(table="exam", field="type"),
    FieldTarget(table="exam", field="result_notes"),
    FieldTarget(table="procedure", field="title"),
    FieldTarget(table="procedure", field="description"),
    FieldTarget(table="procedure", field="notes"),
    FieldTarget(table="doctor_template", field="title"),
    FieldTarget(table="doctor_template", field="body"),
    FieldTarget(table="text_document", field="title"),
    FieldTarget(table="text_document", field="body"),
    FieldTarget(table="evolution", field="content"),
    FieldTarget(table="audit_log", field="before_state"),
    FieldTarget(table="audit_log", field="after_state"),
)


def _validate_identifier(value: str) -> str:
    if not value.replace("_", "").isalnum():
        raise ValueError(f"Invalid SQL identifier: {value}")
    return value


def _is_current_version(ciphertext: str, active_version: str) -> bool:
    return ciphertext.startswith(f"{active_version}:")


async def _load_batch(
    conn: AsyncConnection,
    target: FieldTarget,
    batch_size: int,
    offset: int,
) -> list[dict[str, Any]]:
    table = _validate_identifier(target.table)
    field = _validate_identifier(target.field)
    stmt = text(
        f"""
        SELECT id::text AS id, {field} AS value
        FROM {table}
        WHERE {field} IS NOT NULL
        ORDER BY created_at ASC, id ASC
        LIMIT :limit OFFSET :offset
        """
    )
    result = await conn.execute(stmt, {"limit": batch_size, "offset": offset})
    return [dict(row) for row in result.mappings().all()]


async def _update_value(
    conn: AsyncConnection,
    target: FieldTarget,
    row_id: str,
    encrypted_value: str,
) -> None:
    table = _validate_identifier(target.table)
    field = _validate_identifier(target.field)
    stmt = text(f"UPDATE {table} SET {field} = :value WHERE id::text = :id")
    await conn.execute(stmt, {"value": encrypted_value, "id": row_id})


async def _reencrypt_target(
    conn: AsyncConnection,
    target: FieldTarget,
    batch_size: int,
    dry_run: bool,
    active_version: str,
) -> tuple[int, int]:
    inspected = 0
    updated = 0
    offset = 0

    while True:
        rows = await _load_batch(
            conn=conn,
            target=target,
            batch_size=batch_size,
            offset=offset,
        )
        if not rows:
            break

        for row in rows:
            inspected += 1
            current_value = row["value"]
            if current_value is None:
                continue

            if _is_current_version(current_value, active_version):
                continue

            plaintext = decrypt_text(str(current_value))
            new_value = encrypt_text(plaintext)

            if new_value == current_value:
                continue

            updated += 1
            if not dry_run:
                await _update_value(
                    conn=conn,
                    target=target,
                    row_id=str(row["id"]),
                    encrypted_value=new_value,
                )

        offset += len(rows)

    return inspected, updated


async def run_reencryption(
    batch_size: int = 500,
    dry_run: bool = True,
    only: set[str] | None = None,
) -> int:
    settings = get_settings()
    active_version = settings.encryption_active_key_version
    engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)

    selected_targets = TARGET_FIELDS
    if only:
        selected_targets = tuple(
            target
            for target in TARGET_FIELDS
            if f"{target.table}.{target.field}" in only
        )

    if not selected_targets:
        print("No matching target fields were selected.")
        await engine.dispose()
        return 0

    total_inspected = 0
    total_updated = 0

    try:
        async with engine.connect() as conn:
            tx = await conn.begin()
            for target in selected_targets:
                inspected, updated = await _reencrypt_target(
                    conn=conn,
                    target=target,
                    batch_size=batch_size,
                    dry_run=dry_run,
                    active_version=active_version,
                )
                total_inspected += inspected
                total_updated += updated
                print(
                    f"{target.table}.{target.field}: inspected={inspected} candidates_for_update={updated}"
                )

            if dry_run:
                await tx.rollback()
            else:
                await tx.commit()

    finally:
        await engine.dispose()

    print(
        f"done dry_run={dry_run} inspected={total_inspected} candidates_for_update={total_updated}"
    )
    return total_updated


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Re-encrypt highly sensitive fields in batches")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true", help="Do not persist updates")
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Optional list of targets (example: patient.notes consultation.conduct)",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.batch_size <= 0:
        raise ValueError("--batch-size must be > 0")

    only = set(args.only) if args.only else None
    asyncio.run(run_reencryption(batch_size=args.batch_size, dry_run=args.dry_run, only=only))


if __name__ == "__main__":
    main()
