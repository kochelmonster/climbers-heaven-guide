import { writable } from 'svelte/store'

export const DEFAULT_MAP_PROVIDER_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
export const GOOGLE_MAP_PROVIDER_URL = 'https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'

const LEGACY_GOOGLE_MAP_PROVIDER_URL = 'http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
const MAP_PROVIDER_STORAGE_KEY = 'map-provider-url'
const GOOGLE_PROVIDER_PATTERN = /^https?:\/\/\{s\}\.google\.com\/vt\/lyrs=s&x=\{x\}&y=\{y\}&z=\{z\}$/

/**
 * @param {string | null | undefined} value
 */
export const normalizeMapProviderUrl = (value) => {
	const url = (value ?? '').trim()

	if (!url) {
		return DEFAULT_MAP_PROVIDER_URL
	}

	if (url === LEGACY_GOOGLE_MAP_PROVIDER_URL || GOOGLE_PROVIDER_PATTERN.test(url)) {
		return GOOGLE_MAP_PROVIDER_URL
	}

	return url
}

/**
 * @param {string | null | undefined} value
 */
export const isSatelliteMapProviderUrl = (value) =>
	GOOGLE_PROVIDER_PATTERN.test(normalizeMapProviderUrl(value))

const getInitialMapProviderUrl = () => {
	if (typeof window === 'undefined') {
		return DEFAULT_MAP_PROVIDER_URL
	}

	return normalizeMapProviderUrl(
		window.localStorage.getItem(MAP_PROVIDER_STORAGE_KEY) ?? DEFAULT_MAP_PROVIDER_URL
	)
}

export const mapProviderUrl = writable(getInitialMapProviderUrl())

if (typeof window !== 'undefined') {
	mapProviderUrl.subscribe((value) => {
		window.localStorage.setItem(
			MAP_PROVIDER_STORAGE_KEY,
			normalizeMapProviderUrl(value)
		)
	})
}

/**
 * @param {string | null | undefined} value
 */
export const setMapProviderUrl = (value) => {
	mapProviderUrl.set(normalizeMapProviderUrl(value))
}

export const resetMapProviderUrl = () => {
	setMapProviderUrl(DEFAULT_MAP_PROVIDER_URL)
}

export const useGoogleMapProviderUrl = () => {
	setMapProviderUrl(GOOGLE_MAP_PROVIDER_URL)
}