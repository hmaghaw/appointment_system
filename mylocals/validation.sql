SELECT
    language_code,
    COUNT(*) AS occurrences
FROM
    appointment_db.translations
GROUP BY
    language_code
ORDER BY
    occurrences DESC;