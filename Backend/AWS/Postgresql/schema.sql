-- schema.sql
CREATE TABLE IF NOT EXISTS cohort_memberships (
    cohort_id VARCHAR(50) NOT NULL,
    employee_id VARCHAR(50) NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cohort_id, employee_id)
);

CREATE TABLE IF NOT EXISTS employee_daily_scores (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    cohort_id VARCHAR(50) NOT NULL,
    score NUMERIC(5, 2) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Database Governance Trigger Function: Restrict Cohort Cap to Exactly Four (TOGAF Rule)
CREATE OR REPLACE FUNCTION check_four_person_cap()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT COUNT(*) FROM cohort_memberships WHERE cohort_id = NEW.cohort_id) >= 4 THEN
        RAISE EXCEPTION 'Cohort Governance Boundary Failure: Target track enrollment cannot exceed exactly 4 human operators.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_cohort_size_boundary
BEFORE INSERT ON cohort_memberships
FOR EACH ROW
WHEN (NEW.cohort_id LIKE 'cohort-togaf%')
EXECUTE FUNCTION check_four_person_cap();
