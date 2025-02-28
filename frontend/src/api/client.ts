import { TrainArrival } from "./types";

const API_BASE_URL = "http://localhost:5000/api";

export const api = {
	async getTrainStations(): Promise<string[]> {
		const response = await fetch(`${API_BASE_URL}/trainStations`);
		if (!response.ok) throw new Error("Failed to fetch train stations");
		return response.json();
	},

	async getTrains(station: string): Promise<string[]> {
		const response = await fetch(
			`${API_BASE_URL}/trains?trainStation=${encodeURIComponent(station)}`
		);
		if (!response.ok) throw new Error("Failed to fetch trains");
		return response.json();
	},

	async getTrainArrivals(
		station: string,
		trainName: string
	): Promise<TrainArrival[]> {
		const response = await fetch(
			`${API_BASE_URL}/trainArrivals?trainStation=${encodeURIComponent(
				station
			)}&trainName=${encodeURIComponent(trainName)}`
		);
		if (!response.ok) throw new Error("Failed to fetch train arrivals");
		return response.json();
	},
};
