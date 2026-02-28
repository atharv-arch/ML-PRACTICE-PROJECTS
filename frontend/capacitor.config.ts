/**
 * Capacitor Configuration File
 * 
 * This file controls how Capacitor wraps the web app into a native
 * mobile application. It defines:
 *   - appId: unique identifier for the app (reverse-domain format)
 *   - appName: display name shown on the device
 *   - webDir: directory containing the built web assets (HTML/CSS/JS)
 *   - server: configures how the web content is served inside the native shell
 *
 * For development:
 *   - Set server.url to your local backend URL for live reload
 *   - Set server.cleartext to true to allow HTTP (not just HTTPS)
 *
 * For production:
 *   - Remove server.url so the app uses bundled web assets
 *   - Deploy the FastAPI backend to a public URL (e.g., Render, Railway)
 *   - Set the BACKEND_URL in index.html's APP_CONFIG
 */

import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
    // ── App Identity ────────────────────────────────────────────────
    // Unique package identifier (used by Android/iOS app stores)
    appId: 'com.routineai.app',

    // Display name shown under the app icon on the device home screen
    appName: 'RoutineAI',

    // ── Web Assets Directory ────────────────────────────────────────
    // Path to the mobile-ready web assets directory.
    // 'www' contains HTML/CSS/JS with relative paths for Capacitor's WebView.
    webDir: 'www',

    // ── Server Configuration ────────────────────────────────────────
    server: {
        // Allow HTTP connections (needed for local development)
        // Set to false in production if using HTTPS exclusively
        androidScheme: 'https',

        // DEVELOPMENT ONLY: Uncomment the line below to enable live reload
        // from your local machine. Replace with your computer's local IP.
        // url: 'http://192.168.1.100:8000',

        // Allow cleartext (HTTP) traffic — required for local dev servers
        // cleartext: true,
    },

    // ── Android-Specific Settings ───────────────────────────────────
    android: {
        // Allow mixed content (HTTP + HTTPS) in the WebView
        allowMixedContent: true,

        // Customize the splash screen background color (dark theme match)
        backgroundColor: '#0a0e1a',
    },

    // ── Plugins Configuration ──────────────────────────────────────
    // Add plugin-specific settings here as you integrate native features
    // Example: LocalNotifications for task reminders
    plugins: {
        // SplashScreen plugin: controls the loading splash screen
        SplashScreen: {
            // Duration the splash screen is shown (in milliseconds)
            launchShowDuration: 2000,

            // Auto-hide after the duration
            launchAutoHide: true,

            // Background color matching the app's dark theme
            backgroundColor: '#0a0e1a',

            // Don't show a spinner (the app loads fast)
            showSpinner: false,
        },
    },
};

export default config;
