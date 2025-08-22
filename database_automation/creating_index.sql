CREATE INDEX IF NOT EXISTS idx_wlb_unique_id ON river_levels_bulletin (unique_id);
CREATE INDEX IF NOT EXISTS idx_wlb_source_file ON river_levels_bulletin (source_file);
CREATE INDEX IF NOT EXISTS idx_wlb_river_station ON river_levels_bulletin (river, station);
CREATE INDEX IF NOT EXISTS idx_loc_river_station ON cwc_location (river, station);