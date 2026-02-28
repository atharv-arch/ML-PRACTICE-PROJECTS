/**
 * API Client — Centralized HTTP wrapper for all backend API calls.
 *
 * Provides clean methods for every endpoint with error handling
 * and consistent response formatting.
 */

const API_BASE = '/api';

const api = {
    /**
     * Generic fetch wrapper with error handling.
     */
    async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const config = {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            // Handle 204 No Content
            if (response.status === 204) return null;

            return await response.json();
        } catch (err) {
            console.error(`API Error [${options.method || 'GET'} ${url}]:`, err);
            throw err;
        }
    },

    // ── Task Endpoints ────────────────────────────────────────────

    /** Create a new task */
    createTask(taskData) {
        return this.request('/tasks/', {
            method: 'POST',
            body: JSON.stringify(taskData),
        });
    },

    /** List tasks with optional filters */
    listTasks(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/tasks/?${query}`);
    },

    /** Get a single task by ID */
    getTask(taskId) {
        return this.request(`/tasks/${taskId}`);
    },

    /** Update a task */
    updateTask(taskId, taskData) {
        return this.request(`/tasks/${taskId}`, {
            method: 'PUT',
            body: JSON.stringify(taskData),
        });
    },

    /** Mark a task as completed */
    completeTask(taskId) {
        return this.request(`/tasks/${taskId}/complete`, { method: 'PATCH' });
    },

    /** Delete a task */
    deleteTask(taskId) {
        return this.request(`/tasks/${taskId}`, { method: 'DELETE' });
    },

    /** Get task action logs */
    getTaskLogs(taskId) {
        return this.request(`/tasks/${taskId}/logs`);
    },

    // ── Analytics Endpoints ───────────────────────────────────────

    /** Get dashboard stats */
    getDashboard() {
        return this.request('/analytics/dashboard');
    },

    /** Get hourly productivity data */
    getHourlyProductivity() {
        return this.request('/analytics/hourly');
    },

    /** Get category breakdown stats */
    getCategoryStats() {
        return this.request('/analytics/categories');
    },

    /** Get streak information */
    getStreaks() {
        return this.request('/analytics/streaks');
    },

    /** Get weekly summary */
    getWeeklySummary() {
        return this.request('/analytics/weekly-summary');
    },

    /** Get week-over-week comparison */
    getWeeklyComparison() {
        return this.request('/analytics/weekly-comparison');
    },

    // ── AI Suggestion Endpoints ───────────────────────────────────

    /** Get AI-optimized schedule suggestions */
    getScheduleSuggestions() {
        return this.request('/suggestions/schedule');
    },

    /** Get personalized insights */
    getInsights() {
        return this.request('/suggestions/insights');
    },

    /** Health check */
    healthCheck() {
        return this.request('/health');
    },
};
