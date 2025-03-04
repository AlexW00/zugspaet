import { TrainArrival } from "./types";

const API_BASE_URL =
	import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api";

export const api = {
	async gettrain_stations(): Promise<string[]> {
		const response = await fetch(`${API_BASE_URL}/train_stations`);
		if (!response.ok) throw new Error("Failed to fetch train stations");
		return response.json();
	},

	async getTrains(station: string): Promise<string[]> {
		const response = await fetch(
			`${API_BASE_URL}/trains?train_station=${encodeURIComponent(station)}`
		);
		if (!response.ok) throw new Error("Failed to fetch trains");
		return response.json();
	},

	async getTrainArrivals(
		station: string,
		train_name: string
	): Promise<TrainArrival[]> {
		const response = await fetch(
			`${API_BASE_URL}/train_arrival?train_station=${encodeURIComponent(
				station
			)}&train_name=${encodeURIComponent(train_name)}`
		);
		if (!response.ok) throw new Error("Failed to fetch train arrivals");
		return response.json();
	},

	async getLastImport(): Promise<{ last_import: string | null }> {
		const response = await fetch(`${API_BASE_URL}/last_import`);
		if (!response.ok) throw new Error("Failed to fetch last import time");
		return response.json();
	},
};
