CREATE TABLE IF NOT EXISTS source_runs (
    id BIGSERIAL PRIMARY KEY,
    source_name TEXT NOT NULL,
    query TEXT NOT NULL,
    area_code INTEGER,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    fetched_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'running'
);

CREATE TABLE IF NOT EXISTS companies (
    id BIGSERIAL PRIMARY KEY,
    source_company_id TEXT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS locations (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    country_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vacancies (
    id BIGSERIAL PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_vacancy_id TEXT NOT NULL,
    company_id BIGINT REFERENCES companies(id),
    location_id BIGINT REFERENCES locations(id),
    title TEXT NOT NULL,
    alternate_url TEXT,
    published_at TIMESTAMPTZ,
    schedule TEXT,
    experience TEXT,
    employment TEXT,
    snippet_requirement TEXT,
    snippet_responsibility TEXT,
    raw_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_name, source_vacancy_id)
);

CREATE TABLE IF NOT EXISTS salary_snapshots (
    id BIGSERIAL PRIMARY KEY,
    vacancy_id BIGINT NOT NULL REFERENCES vacancies(id) ON DELETE CASCADE,
    currency TEXT,
    salary_from INTEGER,
    salary_to INTEGER,
    gross BOOLEAN,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
