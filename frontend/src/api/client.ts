import {
	DelayStatistics,
	TimeBasedDelay,
	TopDelay,
	TrainArrival,
} from "./types";

const API_BASE_URL =
	import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api";

export const api = {
	async getStations(train_name?: string): Promise<string[]> {
		const url = new URL(`${API_BASE_URL}/stations`);
		if (train_name) {
			url.searchParams.set("train_name", train_name);
		}
		const response = await fetch(url);
		if (!response.ok) throw new Error("Failed to fetch stations");
		return response.json();
	},

	async getTrains(station?: string): Promise<string[]> {
		const url = new URL(`${API_BASE_URL}/trains`);
		if (station) {
			url.searchParams.set("train_station", station);
		}
		const response = await fetch(url);
		if (!response.ok) throw new Error("Failed to fetch trains");
		return response.json();
	},

	async getArrivals(params: {
		station?: string;
		train_name?: string;
	}): Promise<TrainArrival[]> {
		const url = new URL(`${API_BASE_URL}/arrivals`);
		if (params.station) {
			url.searchParams.set("train_station", params.station);
		}
		if (params.train_name) {
			url.searchParams.set("train_name", params.train_name);
		}
		const response = await fetch(url);
		if (!response.ok) throw new Error("Failed to fetch arrivals");
		return response.json();
	},

	async getLastImport(): Promise<{ last_import: string | null }> {
		const response = await fetch(`${API_BASE_URL}/last_import`);
		if (!response.ok) throw new Error("Failed to fetch last import time");
		return response.json();
	},

	async getDelayStatistics(params: {
		station?: string;
		train_name?: string;
		days?: number;
	}): Promise<DelayStatistics> {
		const url = new URL(`${API_BASE_URL}/stats/delays`);
		if (params.station) {
			url.searchParams.set("train_station", params.station);
		}
		if (params.train_name) {
			url.searchParams.set("train_name", params.train_name);
		}
		if (params.days) {
			url.searchParams.set("days", params.days.toString());
		}
		const response = await fetch(url);
		if (!response.ok) throw new Error("Failed to fetch delay statistics");
		return response.json();
	},

	async getDelaysByTime(params: {
		station?: string;
		train_name?: string;
		group_by?: "hour" | "day" | "month";
		days?: number;
	}): Promise<TimeBasedDelay[]> {
		const url = new URL(`${API_BASE_URL}/stats/delays/by_time`);
		if (params.station) {
			url.searchParams.set("train_station", params.station);
		}
		if (params.train_name) {
			url.searchParams.set("train_name", params.train_name);
		}
		if (params.group_by) {
			url.searchParams.set("group_by", params.group_by);
		}
		if (params.days) {
			url.searchParams.set("days", params.days.toString());
		}
		const response = await fetch(url);
		if (!response.ok) throw new Error("Failed to fetch time-based delays");
		return response.json();
	},

	async getTopDelays(params: {
		type?: "station" | "train";
		limit?: number;
		days?: number;
	}): Promise<TopDelay[]> {
		const url = new URL(`${API_BASE_URL}/stats/top_delays`);
		if (params.type) {
			url.searchParams.set("type", params.type);
		}
		if (params.limit) {
			url.searchParams.set("limit", params.limit.toString());
		}
		if (params.days) {
			url.searchParams.set("days", params.days.toString());
		}
		const response = await fetch(url);
		if (!response.ok) throw new Error("Failed to fetch top delays");
		return response.json();
	},
};
