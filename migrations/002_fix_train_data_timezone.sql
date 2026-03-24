CREATE TABLE IF NOT EXISTS applied_data_fixes (
    name VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM applied_data_fixes
        WHERE name = 'fix_train_data_timezone_v1'
    ) THEN
        -- Existing schedule timestamps were imported from DB plan data as naive
        -- Europe/Berlin times into TIMESTAMP WITH TIME ZONE columns while
        -- Postgres ran in UTC. Reinterpret those stored UTC wall times as
        -- Europe/Berlin wall times.
        UPDATE train_data
        SET
            time = (time AT TIME ZONE 'UTC') AT TIME ZONE 'Europe/Berlin',
            arrival_planned_time = CASE
                WHEN arrival_planned_time IS NULL THEN NULL
                ELSE (arrival_planned_time AT TIME ZONE 'UTC') AT TIME ZONE 'Europe/Berlin'
            END,
            arrival_change_time = CASE
                WHEN arrival_change_time IS NULL THEN NULL
                ELSE (arrival_change_time AT TIME ZONE 'UTC') AT TIME ZONE 'Europe/Berlin'
            END,
            departure_planned_time = CASE
                WHEN departure_planned_time IS NULL THEN NULL
                ELSE (departure_planned_time AT TIME ZONE 'UTC') AT TIME ZONE 'Europe/Berlin'
            END,
            departure_change_time = CASE
                WHEN departure_change_time IS NULL THEN NULL
                ELSE (departure_change_time AT TIME ZONE 'UTC') AT TIME ZONE 'Europe/Berlin'
            END;

        INSERT INTO applied_data_fixes (name)
        VALUES ('fix_train_data_timezone_v1');
    END IF;
END $$;
