-- Create table to track processed dates
CREATE TABLE IF NOT EXISTS processed_dates (
    date DATE PRIMARY KEY,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create table for train data
CREATE TABLE IF NOT EXISTS train_data (
    id SERIAL PRIMARY KEY,
    station VARCHAR(255) NOT NULL,
    train_name VARCHAR(255) NOT NULL,
    final_destination_station VARCHAR(255) NOT NULL,
    delay_in_min INTEGER,
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    is_canceled BOOLEAN NOT NULL DEFAULT FALSE,
    train_type VARCHAR(50) NOT NULL,
    train_line_ride_id VARCHAR(255) NOT NULL,
    train_line_station_num INTEGER NOT NULL,
    arrival_planned_time TIMESTAMP WITH TIME ZONE,
    arrival_change_time TIMESTAMP WITH TIME ZONE,
    departure_planned_time TIMESTAMP WITH TIME ZONE,
    departure_change_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_train_data_station ON train_data(station);
CREATE INDEX IF NOT EXISTS idx_train_data_train_name ON train_data(train_name);
CREATE INDEX IF NOT EXISTS idx_train_data_final_destination ON train_data(final_destination_station);
CREATE INDEX IF NOT EXISTS idx_train_data_delay ON train_data(delay_in_min);
CREATE INDEX IF NOT EXISTS idx_train_data_train_type ON train_data(train_type);
CREATE INDEX IF NOT EXISTS idx_train_data_train_line_ride_id ON train_data(train_line_ride_id);
CREATE INDEX IF NOT EXISTS idx_train_data_arrival_planned ON train_data(arrival_planned_time);
CREATE INDEX IF NOT EXISTS idx_train_data_departure_planned ON train_data(departure_planned_time);

-- Create some useful composite indices for common query patterns
CREATE INDEX IF NOT EXISTS idx_train_data_station_train ON train_data(station, train_name);
