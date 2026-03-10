from sqlalchemy import create_engine, inspect, text


def get_db_context(url: str, skip_tables: list[str]) -> str:
    engine = create_engine(url)
    insp = inspect(engine)

    blocks: list[str] = []

    # Views
    views = insp.get_view_names()
    for view in views:
        blocks.append(f'<view name="{view}" />')

    # Tables
    for table in insp.get_table_names():
        if table in skip_tables:
            continue

        lines: list[str] = []

        # Columns
        for col in insp.get_columns(table):
            nullable = "nullable" if col["nullable"] else "not null"
            default = (
                f' default="{col["default"]}"' if col["default"] is not None else ""
            )
            lines.append(
                f'  <column name="{col["name"]}" type="{col["type"]}" {nullable}{default}/>'
            )

        # Primary key
        pk = insp.get_pk_constraint(table)
        if pk["constrained_columns"]:
            cols = ", ".join(pk["constrained_columns"])
            lines.append(f'  <primary_key columns="{cols}" />')

        # Foreign keys
        for fk in insp.get_foreign_keys(table):
            lines.append(
                f'  <foreign_key columns="{", ".join(fk["constrained_columns"])}"'
                f' references="{fk["referred_table"]}({", ".join(fk["referred_columns"])})" />'
            )

        # Indexes
        for idx in insp.get_indexes(table):
            unique = ' unique="true"' if idx["unique"] else ""
            cols = ", ".join(idx["column_names"])
            lines.append(f'  <index name="{idx["name"]}" columns="{cols}"{unique} />')

        inner = "\n".join(lines)
        blocks.append(f'<table name="{table}">\n{inner}\n</table>')

    # Sequences (PostgreSQL only)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT sequence_name FROM information_schema.sequences "
                    "WHERE sequence_schema = 'public'"
                )
            ).fetchall()
            for row in rows:
                blocks.append(f'<sequence name="{row[0]}" />')
    except Exception:
        pass

    engine.dispose()
    return "\n\n".join(blocks)
