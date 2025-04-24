# TODO: verify this works as eexprcted with some test cases
DELETE FROM papers
WHERE
    id in (
        SELECT
            id
        FROM
            (
                SELECT
                    id,
                    title,
                    summary,
                    chunk,
                    row_number() OVER (
                        PARTITION BY
                            title,
                            summary,
                            chunk,
                            embedding
                        ORDER BY
                            id
                    )
                FROM
                    papers
            )
        WHERE
            row_number >= 2
    );