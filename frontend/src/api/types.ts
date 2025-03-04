export interface TrainArrival {
	delay_in_min: number;
	time: string;
	final_destination_station: string;
	is_canceled: boolean;
}

export interface ApiError {
	error: string;
}
