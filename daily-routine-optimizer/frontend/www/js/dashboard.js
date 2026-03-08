/**
 * Dashboard View — Main productivity overview with stat cards and charts.
 *
 * Displays:
 *   - Key stat cards (completion rate, streak, tasks today, etc.)
 *   - Hourly productivity bar chart
 *   - Recent activity feed
 */

const DashboardView = {
    charts: {},

    /**
     * Render the dashboard view into the page container.
     */
    async render(container) {
        container.innerHTML = `
            <div class="fade-in">
                <!-- Stat Cards Grid -->
                <div class="stats-grid" id="stats-grid">
                    <div class="stat-card">
                        <span class="stat-icon">📋</span>
                        <div class="stat-value" id="stat-total">—</div>
                        <div class="stat-label">Total Tasks</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-icon">✅</span>
                        <div class="stat-value" id="stat-completed">—</div>
                        <div class="stat-label">Completed</div>
                        <div class="stat-change positive" id="stat-rate">—</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-icon">🔥</span>
                        <div class="stat-value" id="stat-streak">—</div>
                        <div class="stat-label">Day Streak</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-icon">⏰</span>
                        <div class="stat-value" id="stat-productive-hour">—</div>
                        <div class="stat-label">Peak Hour</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-icon">📅</span>
                        <div class="stat-value" id="stat-today">—</div>
                        <div class="stat-label">Today's Tasks</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-icon">⏱️</span>
                        <div class="stat-value" id="stat-delay">—</div>
                        <div class="stat-label">Avg Delay</div>
                    </div>
                </div>

                <!-- Charts Row -->
                <div class="charts-grid">
                    <div class="chart-card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">Hourly Productivity</div>
                                <div class="card-subtitle">Task completions by hour of day</div>
                            </div>
                        </div>
                        <canvas id="hourly-chart"></canvas>
                    </div>
                    <div class="chart-card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">Weekly Trend</div>
                                <div class="card-subtitle">Completion rates over the last 4 weeks</div>
                            </div>
                        </div>
                        <canvas id="weekly-chart"></canvas>
                    </div>
                </div>

                <!-- Recent Tasks -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Recent Tasks</div>
                        <a href="#tasks" class="btn btn-ghost btn-sm">View All →</a>
                    </div>
                    <div class="task-list" id="recent-tasks">
                        <div class="empty-state">
                            <div class="spinner"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        await this.loadData();
    },

    /**
     * Load all dashboard data from the API.
     */
    async loadData() {
        try {
            const [stats, hourly, weekly, tasks] = await Promise.all([
                api.getDashboard(),
                api.getHourlyProductivity(),
                api.getWeeklyComparison(),
                api.listTasks({ per_page: 5 }),
            ]);

            this.renderStats(stats);
            this.renderHourlyChart(hourly);
            this.renderWeeklyChart(weekly);
            this.renderRecentTasks(tasks.tasks || []);
        } catch (err) {
            console.error('Dashboard load failed:', err);
        }
    },

    /**
     * Populate dashboard stat cards.
     */
    renderStats(stats) {
        document.getElementById('stat-total').textContent = stats.total_tasks;
        document.getElementById('stat-completed').textContent = stats.completed_tasks;
        document.getElementById('stat-rate').textContent = `${stats.completion_rate.toFixed(0)}% rate`;
        document.getElementById('stat-streak').textContent = `${stats.current_streak} days`;
        document.getElementById('stat-productive-hour').textContent = this.formatHour(stats.most_productive_hour);
        document.getElementById('stat-today').textContent = `${stats.completed_today}/${stats.tasks_today}`;

        const delayEl = document.getElementById('stat-delay');
        const delay = stats.avg_delay_minutes;
        delayEl.textContent = delay > 0 ? `+${delay.toFixed(0)}m` : `${delay.toFixed(0)}m`;
    },

    /**
     * Render the hourly productivity bar chart.
     */
    renderHourlyChart(hourlyData) {
        const ctx = document.getElementById('hourly-chart');
        if (!ctx) return;

        // Destroy existing chart instance
        if (this.charts.hourly) this.charts.hourly.destroy();

        const labels = hourlyData.map(h => this.formatHour(h.hour));
        const data = hourlyData.map(h => h.completed_count);
        const colors = hourlyData.map(h => {
            if (h.completed_count >= 3) return 'rgba(99, 102, 241, 0.8)';
            if (h.completed_count >= 1) return 'rgba(99, 102, 241, 0.5)';
            return 'rgba(99, 102, 241, 0.15)';
        });

        this.charts.hourly = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Completed Tasks',
                    data,
                    backgroundColor: colors,
                    borderRadius: 6,
                    borderSkipped: false,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12,
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#64748b', stepSize: 1 },
                        grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    },
                    x: {
                        ticks: { color: '#64748b', maxRotation: 45 },
                        grid: { display: false },
                    },
                },
            },
        });
    },

    /**
     * Render the weekly comparison chart.
     */
    renderWeeklyChart(weeklyData) {
        const ctx = document.getElementById('weekly-chart');
        if (!ctx) return;

        if (this.charts.weekly) this.charts.weekly.destroy();

        this.charts.weekly = new Chart(ctx, {
            type: 'line',
            data: {
                labels: weeklyData.map(w => w.week_label),
                datasets: [{
                    label: 'Completion Rate',
                    data: weeklyData.map(w => w.completion_rate),
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#6366f1',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                        callbacks: {
                            label: (ctx) => `${ctx.parsed.y.toFixed(1)}% completion`,
                        },
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { color: '#64748b', callback: v => `${v}%` },
                        grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    },
                    x: {
                        ticks: { color: '#64748b' },
                        grid: { display: false },
                    },
                },
            },
        });
    },

    /**
     * Render the recent tasks list.
     */
    renderRecentTasks(tasks) {
        const container = document.getElementById('recent-tasks');
        if (!container) return;

        if (tasks.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📋</div>
                    <div class="empty-state-title">No tasks yet</div>
                    <div class="empty-state-desc">Create your first task to get started!</div>
                </div>
            `;
            return;
        }

        container.innerHTML = tasks.map(task => `
            <div class="task-item ${task.status === 'completed' ? 'completed' : ''}"
                 data-task-id="${task.id}">
                <div class="task-check" onclick="event.stopPropagation(); TasksView.toggleTask(${task.id}, '${task.status}')">
                    ${task.status === 'completed' ? '✓' : ''}
                </div>
                <div class="task-item-content">
                    <div class="task-item-title">${this.escapeHtml(task.title)}</div>
                    <div class="task-item-meta">
                        <span class="task-badge category">${task.category}</span>
                        <span class="task-badge priority-${task.priority}">P${task.priority}</span>
                        ${task.assigned_time ? `<span>⏰ ${this.formatTime(task.assigned_time)}</span>` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    },

    // ── Helpers ────────────────────────────────────────────────────

    formatHour(hour) {
        if (hour === 0) return '12AM';
        if (hour < 12) return `${hour}AM`;
        if (hour === 12) return '12PM';
        return `${hour - 12}PM`;
    },

    formatTime(isoString) {
        if (!isoString) return '';
        const d = new Date(isoString);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },

    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    /** Clean up chart instances when leaving the view */
    destroy() {
        Object.values(this.charts).forEach(c => c?.destroy());
        this.charts = {};
    },
};
