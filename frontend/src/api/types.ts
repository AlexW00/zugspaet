export interface TrainArrival {
	delayInMin: number;
	time: string;
	finalDestinationStation: string;
	isCanceled: boolean;
}

export interface ApiError {
	error: string;
}
