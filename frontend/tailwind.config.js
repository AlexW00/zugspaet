/** @type {import('tailwindcss').Config} */
export default {
	content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
	theme: {
		extend: {
			colors: {
				"db-red": {
					50: "#fff1f1",
					100: "#ffdfdf",
					200: "#ffc5c5",
					300: "#ff9d9d",
					400: "#ff6464",
					500: "#ff2d2d",
					600: "#ec0000", // Deutsche Bahn Red
					700: "#c70000",
					800: "#a40606",
					900: "#880c0c",
					950: "#4b0000",
				},
			},
		},
	},
	plugins: [],
};
