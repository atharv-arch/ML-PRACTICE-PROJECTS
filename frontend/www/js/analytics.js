/**
 * Analytics View — Detailed productivity charts and statistics.
 *
 * Displays:
 *   - Hourly productivity heatmap/bar chart
 *   - Category breakdown doughnut chart
 *   - Weekly comparison bar chart
 *   - Streak timeline
 */

const AnalyticsView = {
    charts: {},

    async render(container) {
        container.innerHTML = `
            <div class="fade-in">
                <!-- Summary Stats -->
                <div class="stats-grid" id="analytics-stats">
                    <div class="stat-card">
                        <span class="stat-icon">📊</span>
                        <div class="stat-value" id="analytics-rate">—</div>
                        <div class="stat-label">Overall Rate</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-icon">⏱️</span>
                        <div class="stat-value" id="analytics-delay">—</div>
                        <div class="stat-label">Avg Delay</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-icon">🔥</span>
                        <div class="stat-value" id="analytics-streak">—</div>
                        <div class="stat-label">Best Streak</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-icon">⭐</span>
                        <div class="stat-value" id="analytics-peak">—</div>
                        <div class="stat-label">Peak Hour</div>
                    </div>
                </div>

                <!-- Charts -->
                <div class="charts-grid">
                    <div class="chart-card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">Hourly Productivity</div>
                                <div class="card-subtitle">Completion rate per hour of day</div>
                            </div>
                        </div>
                        <canvas id="analytics-hourly-chart"></canvas>
                    </div>
                    <div class="chart-card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">Category Breakdown</div>
                                <div class="card-subtitle">Tasks by category</div>
                            </div>
                        </div>
                        <canvas id="analytics-category-chart"></canvas>
                    </div>
                </div>

                <div class="charts-grid">
                    <div class="chart-card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">Weekly Comparison</div>
                                <div class="card-subtitle">Completed vs total tasks per week</div>
                            </div>
                        </div>
                        <canvas id="analytics-weekly-chart"></canvas>
                    </div>
                    <div class="chart-card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">Streak History</div>
                                <div class="card-subtitle">Daily completion rate (last 14 days)</div>
                            </div>
                        </div>
                        <canvas id="analytics-streak-chart"></canvas>
                    </div>
                </div>

                <!-- Weekly Summary -->
                <div class="card" style="margin-top: 4px;">
                    <div class="card-header">
                        <div class="card-title">📋 Weekly Summary & Recommendations</div>
                    </div>
                    <div id="weekly-recommendations"></div>
                </div>
            </div>
        `;

        await this.loadData();
    },

    async loadData() {
        try {
            const [dashboard, hourly, categories, weekly, streaks, summary] = await Promise.all([
                api.getDashboard(),
                api.getHourlyProductivity(),
                api.getCategoryStats(),
                api.getWeeklyComparison(),
                api.getStreaks(),
                api.getWeeklySummary(),
            ]);

            this.renderStats(dashboard, streaks);
            this.renderHourlyChart(hourly);
            this.renderCategoryChart(categories);
            this.renderWeeklyChart(weekly);
            this.renderStreakChart(streaks);
            this.renderRecommendations(summary);
        } catch (err) {
            console.error('Analytics load failed:', err);
        }
    },

    renderStats(dashboard, streaks) {
        document.getElementById('analytics-rate').textContent = `${dashboard.completion_rate.toFixed(0)}%`;
        document.getElementById('analytics-delay').textContent =
            dashboard.avg_delay_minutes > 0
                ? `+${dashboard.avg_delay_minutes.toFixed(0)}m`
                : `${dashboard.avg_delay_minutes.toFixed(0)}m`;
        document.getElementById('analytics-streak').textContent = `${streaks.longest_streak} days`;
        document.getElementById('analytics-peak').textContent = this.formatHour(dashboard.most_productive_hour);
    },

    renderHourlyChart(hourlyData) {
        const ctx = document.getElementById('analytics-hourly-chart');
        if (!ctx) return;
        if (this.charts.hourly) this.charts.hourly.destroy();

        // Color gradient: low = dim, high = vibrant
        const maxRate = Math.max(...hourlyData.map(h => h.completion_rate), 1);
        const colors = hourlyData.map(h => {
            const intensity = h.completion_rate / maxRate;
            return `rgba(99, 102, 241, ${0.15 + intensity * 0.7})`;
        });

        this.charts.hourly = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: hourlyData.map(h => this.formatHour(h.hour)),
                datasets: [{
                    label: 'Completion Rate',
                    data: hourlyData.map(h => h.completion_rate),
                    backgroundColor: colors,
                    borderRadius: 6,
                    borderSkipped: false,
                }],
            },
            options: this.chartOptions({
                yCallback: v => `${v}%`,
                yMax: 100,
            }),
        });
    },

    renderCategoryChart(categories) {
        const ctx = document.getElementById('analytics-category-chart');
        if (!ctx) return;
        if (this.charts.category) this.charts.category.destroy();

        const catColors = {
            work: '#6366f1', health: '#22c55e', personal: '#f59e0b',
            learning: '#3b82f6', errands: '#8b5cf6', general: '#64748b',
        };

        this.charts.category = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: categories.map(c => c.category),
                datasets: [{
                    data: categories.map(c => c.total),
                    backgroundColor: categories.map(c => catColors[c.category] || '#64748b'),
                    borderWidth: 0,
                    hoverOffset: 8,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#94a3b8', padding: 16, usePointStyle: true },
                    },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                        callbacks: {
                            label: (ctx) => {
                                const cat = categories[ctx.dataIndex];
                                return `${cat.category}: ${cat.total} tasks (${cat.completion_rate.toFixed(0)}% done)`;
                            },
                        },
                    },
                },
            },
        });
    },

    renderWeeklyChart(weekly) {
        const ctx = document.getElementById('analytics-weekly-chart');
        if (!ctx) return;
        if (this.charts.weekly) this.charts.weekly.destroy();

        this.charts.weekly = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: weekly.map(w => w.week_label),
                datasets: [
                    {
                        label: 'Completed',
                        data: weekly.map(w => w.completed_tasks),
                        backgroundColor: 'rgba(34, 197, 94, 0.7)',
                        borderRadius: 6,
                    },
                    {
                        label: 'Total',
                        data: weekly.map(w => w.total_tasks),
                        backgroundColor: 'rgba(99, 102, 241, 0.3)',
                        borderRadius: 6,
                    },
                ],
            },
            options: this.chartOptions({ yCallback: v => v }),
        });
    },

    renderStreakChart(streaks) {
        const ctx = document.getElementById('analytics-streak-chart');
        if (!ctx) return;
        if (this.charts.streak) this.charts.streak.destroy();

        const history = streaks.streak_history || [];

        this.charts.streak = new Chart(ctx, {
            type: 'line',
            data: {
                labels: history.map(h => {
                    const d = new Date(h.date);
                    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
                }),
                datasets: [{
                    label: 'Daily Completion Rate',
                    data: history.map(h => h.rate ?? 0),
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointBackgroundColor: history.map(h =>
                        h.in_streak ? '#22c55e' : '#64748b'
                    ),
                }, {
                    label: 'Streak Threshold',
                    data: history.map(() => 80),
                    borderColor: 'rgba(245, 158, 11, 0.4)',
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false,
                }],
            },
            options: this.chartOptions({ yCallback: v => `${v}%`, yMax: 100 }),
        });
    },

    renderRecommendations(summary) {
        const container = document.getElementById('weekly-recommendations');
        if (!container) return;

        let recs = [];
        try {
            recs = JSON.parse(summary.recommendations || '[]');
        } catch { recs = []; }

        if (recs.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="padding: 30px;">
                    <div class="empty-state-icon">💡</div>
                    <div class="empty-state-title">No recommendations yet</div>
                    <div class="empty-state-desc">Complete more tasks to receive personalized recommendations.</div>
                </div>
            `;
            return;
        }

        const iconMap = { tip: '💡', warning: '⚠️', achievement: '🏆' };
        container.innerHTML = recs.map(rec => `
            <div class="insight-card ${rec.type}">
                <span class="insight-icon">${iconMap[rec.type] || '💡'}</span>
                <div>
                    <div class="insight-title">${rec.title}</div>
                    <div class="insight-desc">${rec.description}</div>
                </div>
            </div>
        `).join('');
    },

    // ── Helpers ────────────────────────────────────────────────────

    chartOptions({ yCallback = v => v, yMax = undefined } = {}) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8' },
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    cornerRadius: 8,
                    padding: 12,
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: yMax,
                    ticks: { color: '#64748b', callback: yCallback },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                },
                x: {
                    ticks: { color: '#64748b', maxRotation: 45 },
                    grid: { display: false },
                },
            },
        };
    },

    formatHour(hour) {
        if (hour === 0) return '12AM';
        if (hour < 12) return `${hour}AM`;
        if (hour === 12) return '12PM';
        return `${hour - 12}PM`;
    },

    destroy() {
        Object.values(this.charts).forEach(c => c?.destroy());
        this.charts = {};
    },
};
