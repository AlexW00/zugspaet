export interface TrainArrival {
	delay_in_min: number;
	time: string;
	final_destination_station: string;
	is_canceled: boolean;
}

export interface ApiError {
	error: string;
}

export interface DelayStatistics {
	avg_delay: number;
	min_delay: number;
	max_delay: number;
	median_delay: number;
	total_arrivals: number;
	delayed_arrivals: number;
	ontime_arrivals: number;
}

export interface TimeBasedDelay {
	time_group: number;
	avg_delay: number;
	total_arrivals: number;
	delayed_arrivals: number;
}

export interface TopDelay {
	name: string;
	avg_delay: number;
	total_arrivals: number;
	delayed_arrivals: number;
	delay_percentage: number;
}
