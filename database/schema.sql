
-- CRISISCORE DATABASE SCHEMA
-- PostgreSQL + PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;


-- 1. DISTRICTS

CREATE TABLE districts (
    district_id SERIAL PRIMARY KEY,

    state VARCHAR(50) NOT NULL,

    district_name VARCHAR(100) NOT NULL,

    atlas_exposure_rank INT,

    -- District boundary
    boundary GEOMETRY(MULTIPOLYGON, 4326)
);


-- 2. LANDSLIDE EVENTS

CREATE TABLE landslide_events (
    event_id VARCHAR(20) PRIMARY KEY,

    district_id INT REFERENCES districts(district_id),

    event_date DATE,

    area_or_location VARCHAR(200),

    -- Exact geographic location
    location GEOMETRY(POINT, 4326),

    landslide_type VARCHAR(100),

    trigger VARCHAR(100),

    damage_or_impact TEXT,

    source TEXT,

    source_type VARCHAR(50)
);


-- 3. RAINFALL

CREATE TABLE rainfall (
    rainfall_id SERIAL PRIMARY KEY,

    district_id INT REFERENCES districts(district_id),

    recorded_date DATE NOT NULL,

    rainfall_24h DECIMAL(10,2),

    rainfall_3day DECIMAL(10,2),

    rainfall_7day DECIMAL(10,2),

    rainfall_30day DECIMAL(10,2),

    -- Location of rainfall grid cell
    location GEOMETRY(POINT, 4326),

    source TEXT
);


-- 4. TERRAIN


CREATE TABLE terrain (
    terrain_id SERIAL PRIMARY KEY,

    district_id INT REFERENCES districts(district_id),

    location GEOMETRY(POINT, 4326),

    elevation DECIMAL(10,2),

    slope DECIMAL(10,2),

    aspect DECIMAL(10,2),

    curvature DECIMAL(10,2),

    soil_moisture DECIMAL(10,4),

    source TEXT
);


-- 5. RISK PREDICTIONS

CREATE TABLE risk_predictions (
    prediction_id SERIAL PRIMARY KEY,

    district_id INT REFERENCES districts(district_id),

    prediction_time TIMESTAMP,

    risk_probability DECIMAL(5,4),

    risk_score DECIMAL(5,2),

    risk_level VARCHAR(20),

    model_version VARCHAR(50),

    location GEOMETRY(POINT, 4326)
);


-- 6. AUTHORITIES

CREATE TABLE authorities (
    authority_id SERIAL PRIMARY KEY,

    name VARCHAR(200) NOT NULL,

    authority_type VARCHAR(100),

    state VARCHAR(50),

    district VARCHAR(100),

    location GEOMETRY(POINT, 4326),

    contact VARCHAR(100),

    source TEXT
);

-- SPATIAL INDEXES

CREATE INDEX idx_district_boundary
ON districts
USING GIST (boundary);


CREATE INDEX idx_landslide_location
ON landslide_events
USING GIST (location);


CREATE INDEX idx_rainfall_location
ON rainfall
USING GIST (location);


CREATE INDEX idx_terrain_location
ON terrain
USING GIST (location);


CREATE INDEX idx_prediction_location
ON risk_predictions
USING GIST (location);


CREATE INDEX idx_authority_location
ON authorities
USING GIST (location);