/**
 * AI Suggestions View — ML-powered schedule optimization and insights.
 *
 * Displays:
 *   - AI-generated schedule suggestions with confidence scores
 *   - Personalized productivity insights
 *   - Accept/dismiss actions for suggestions
 */

const SuggestionsView = {
    async render(container) {
        container.innerHTML = `
            <div class="fade-in">
                <!-- AI Status Banner -->
                <div class="card" style="margin-bottom: 20px; border-left: 3px solid var(--accent-primary);">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 32px;">🤖</span>
                        <div>
                            <div class="card-title">AI Schedule Optimizer</div>
                            <div class="card-subtitle" id="ai-status">Analyzing your productivity patterns...</div>
                        </div>
                    </div>
                </div>

                <!-- Schedule Suggestions -->
                <div class="section-header">
                    <h2 class="section-title">📅 Suggested Schedule</h2>
                    <button class="btn btn-secondary btn-sm" onclick="SuggestionsView.refresh()">🔄 Refresh</button>
                </div>
                <div id="suggestions-list">
                    <div class="empty-state"><div class="spinner"></div></div>
                </div>

                <!-- Insights -->
                <div class="section-header" style="margin-top: 32px;">
                    <h2 class="section-title">💡 Personalized Insights</h2>
                </div>
                <div id="insights-list">
                    <div class="empty-state"><div class="spinner"></div></div>
                </div>
            </div>
        `;

        await this.loadData();
    },

    async loadData() {
        try {
            const [scheduleData, insightsData] = await Promise.all([
                api.getScheduleSuggestions(),
                api.getInsights(),
            ]);

            this.renderSuggestions(scheduleData);
            this.renderInsights(insightsData);
        } catch (err) {
            console.error('Suggestions load failed:', err);
        }
    },

    renderSuggestions(data) {
        const container = document.getElementById('suggestions-list');
        const statusEl = document.getElementById('ai-status');
        if (!container) return;

        // Update AI status
        if (statusEl) {
            statusEl.textContent = data.model_available
                ? '✅ ML model active — suggestions based on your patterns'
                : '📊 Using rule-based suggestions — keep completing tasks to train your AI model';
        }

        const suggestions = data.suggestions || [];

        if (suggestions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🎯</div>
                    <div class="empty-state-title">No pending tasks to optimize</div>
                    <div class="empty-state-desc">Add some tasks and the AI will suggest the best schedule for you.</div>
                </div>
            `;
            return;
        }

        container.innerHTML = suggestions.map((s, i) => `
            <div class="suggestion-card" style="animation-delay: ${i * 0.05}s;">
                <div class="suggestion-icon">
                    ${s.priority >= 4 ? '🔴' : s.priority >= 3 ? '🟡' : '🟢'}
                </div>
                <div class="suggestion-content">
                    <div class="suggestion-title">${this.escapeHtml(s.task_title)}</div>
                    <div class="suggestion-desc">${s.reason}</div>
                    <div class="suggestion-meta">
                        <span>⏰ Suggested: <strong>${this.formatTime(s.suggested_time)}</strong></span>
                        ${s.current_time ? `<span>📌 Current: ${this.formatTime(s.current_time)}</span>` : ''}
                        <span>⏱ ${s.duration_minutes}min</span>
                        <span>
                            Confidence:
                            <span class="confidence-bar">
                                <span class="confidence-fill" style="width: ${s.confidence * 100}%"></span>
                            </span>
                            ${(s.confidence * 100).toFixed(0)}%
                        </span>
                    </div>
                </div>
                <div class="suggestion-actions">
                    <button class="btn btn-success btn-sm"
                            onclick="SuggestionsView.acceptSuggestion(${s.task_id}, '${s.suggested_time}')"
                            title="Apply this suggestion">
                        ✓ Apply
                    </button>
                    <button class="btn btn-ghost btn-sm"
                            onclick="SuggestionsView.dismissSuggestion(this)"
                            title="Dismiss">
                        ✕
                    </button>
                </div>
            </div>
        `).join('');
    },

    renderInsights(data) {
        const container = document.getElementById('insights-list');
        if (!container) return;

        const insights = data.insights || [];

        if (insights.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">💡</div>
                    <div class="empty-state-title">Insights coming soon</div>
                    <div class="empty-state-desc">Complete more tasks to generate personalized insights.</div>
                </div>
            `;
            return;
        }

        const iconMap = { tip: '💡', warning: '⚠️', achievement: '🏆' };
        container.innerHTML = insights.map(insight => `
            <div class="insight-card ${insight.type}">
                <span class="insight-icon">${iconMap[insight.type] || '💡'}</span>
                <div>
                    <div class="insight-title">${insight.title}</div>
                    <div class="insight-desc">${insight.description}</div>
                    ${insight.metric_value !== null && insight.metric_value !== undefined
                ? `<div style="margin-top: 6px; font-size: 12px; color: var(--text-muted);">
                             Metric: ${typeof insight.metric_value === 'number' ? insight.metric_value.toFixed(1) : insight.metric_value}
                           </div>`
                : ''}
                </div>
            </div>
        `).join('');
    },

    /** Apply a suggestion by updating the task's assigned time */
    async acceptSuggestion(taskId, suggestedTime) {
        try {
            await api.updateTask(taskId, { assigned_time: suggestedTime });
            App.showToast('Schedule updated! ✅', 'success');
            await this.loadData();
        } catch (err) {
            App.showToast(err.message, 'error');
        }
    },

    /** Dismiss a suggestion card with animation */
    dismissSuggestion(button) {
        const card = button.closest('.suggestion-card');
        if (card) {
            card.style.opacity = '0';
            card.style.transform = 'translateX(50px)';
            card.style.transition = 'all 0.3s ease';
            setTimeout(() => card.remove(), 300);
        }
    },

    async refresh() {
        const container = document.getElementById('suggestions-list');
        if (container) {
            container.innerHTML = '<div class="empty-state"><div class="spinner"></div></div>';
        }
        await this.loadData();
        App.showToast('Suggestions refreshed', 'info');
    },

    // ── Helpers ────────────────────────────────────────────────────

    formatTime(isoString) {
        if (!isoString) return '—';
        const d = new Date(isoString);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) +
            ' · ' + d.toLocaleDateString([], { month: 'short', day: 'numeric' });
    },

    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    destroy() { },
};
