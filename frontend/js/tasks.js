/**
 * Tasks View — Full task management with filters and CRUD.
 *
 * Displays:
 *   - Filter bar (status, category)
 *   - Sortable task list
 *   - Task completion, edit, and delete
 */

const TasksView = {
    currentFilter: 'all',
    tasks: [],

    async render(container) {
        container.innerHTML = `
            <div class="fade-in">
                <div class="filters-bar" id="task-filters">
                    <span class="filter-chip active" data-filter="all">All</span>
                    <span class="filter-chip" data-filter="pending">Pending</span>
                    <span class="filter-chip" data-filter="completed">Completed</span>
                    <span class="filter-chip" data-filter="missed">Missed</span>
                    <span style="flex: 1;"></span>
                    <span class="filter-chip" data-cat="work">🏢 Work</span>
                    <span class="filter-chip" data-cat="health">🏃 Health</span>
                    <span class="filter-chip" data-cat="personal">🏠 Personal</span>
                    <span class="filter-chip" data-cat="learning">📚 Learning</span>
                    <span class="filter-chip" data-cat="errands">🛒 Errands</span>
                </div>
                <div class="task-list" id="tasks-list">
                    <div class="empty-state"><div class="spinner"></div></div>
                </div>
            </div>
        `;

        this.bindFilters();
        await this.loadTasks();
    },

    bindFilters() {
        const filters = document.getElementById('task-filters');
        if (!filters) return;

        filters.addEventListener('click', (e) => {
            const chip = e.target.closest('.filter-chip');
            if (!chip) return;

            if (chip.dataset.filter) {
                // Status filter
                filters.querySelectorAll('[data-filter]').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                this.currentFilter = chip.dataset.filter;
                this.renderTasks();
            } else if (chip.dataset.cat) {
                // Category filter toggle
                chip.classList.toggle('active');
                this.renderTasks();
            }
        });
    },

    async loadTasks() {
        try {
            const data = await api.listTasks({ per_page: 100 });
            this.tasks = data.tasks || [];
            this.renderTasks();
        } catch (err) {
            console.error('Failed to load tasks:', err);
            App.showToast('Failed to load tasks', 'error');
        }
    },

    renderTasks() {
        const container = document.getElementById('tasks-list');
        if (!container) return;

        // Apply status filter
        let filtered = this.tasks;
        if (this.currentFilter !== 'all') {
            filtered = filtered.filter(t => t.status === this.currentFilter);
        }

        // Apply category filters
        const activeCategories = Array.from(
            document.querySelectorAll('.filter-chip[data-cat].active')
        ).map(c => c.dataset.cat);

        if (activeCategories.length > 0) {
            filtered = filtered.filter(t => activeCategories.includes(t.category));
        }

        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📋</div>
                    <div class="empty-state-title">No tasks found</div>
                    <div class="empty-state-desc">
                        ${this.currentFilter === 'all'
                    ? 'Create your first task to get started!'
                    : `No ${this.currentFilter} tasks. Try a different filter.`}
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = filtered.map(task => `
            <div class="task-item ${task.status === 'completed' ? 'completed' : ''}"
                 data-task-id="${task.id}">
                <div class="task-check"
                     onclick="event.stopPropagation(); TasksView.toggleTask(${task.id}, '${task.status}')"
                     title="${task.status === 'completed' ? 'Completed' : 'Click to complete'}">
                    ${task.status === 'completed' ? '✓' : ''}
                </div>
                <div class="task-item-content" onclick="TasksView.editTask(${task.id})">
                    <div class="task-item-title">${this.escapeHtml(task.title)}</div>
                    <div class="task-item-meta">
                        <span class="task-badge category">${task.category}</span>
                        <span class="task-badge priority-${task.priority}">P${task.priority}</span>
                        <span>⏱ ${task.duration_minutes}min</span>
                        ${task.assigned_time ? `<span>⏰ ${this.formatDateTime(task.assigned_time)}</span>` : ''}
                    </div>
                </div>
                <div class="task-actions">
                    <button class="task-action-btn" onclick="event.stopPropagation(); TasksView.editTask(${task.id})" title="Edit">✏️</button>
                    <button class="task-action-btn" onclick="event.stopPropagation(); TasksView.deleteTask(${task.id})" title="Delete">🗑️</button>
                </div>
            </div>
        `).join('');
    },

    /** Toggle a task's completed status */
    async toggleTask(taskId, currentStatus) {
        try {
            if (currentStatus !== 'completed') {
                await api.completeTask(taskId);
                App.showToast('Task completed! 🎉', 'success');
            } else {
                await api.updateTask(taskId, { status: 'pending' });
                App.showToast('Task reopened', 'info');
            }
            await this.loadTasks();
        } catch (err) {
            App.showToast(err.message, 'error');
        }
    },

    /** Open the edit modal for a task */
    async editTask(taskId) {
        try {
            const task = await api.getTask(taskId);
            App.openTaskModal(task);
        } catch (err) {
            App.showToast('Failed to load task', 'error');
        }
    },

    /** Delete a task with confirmation */
    async deleteTask(taskId) {
        if (!confirm('Delete this task?')) return;
        try {
            await api.deleteTask(taskId);
            App.showToast('Task deleted', 'info');
            await this.loadTasks();
        } catch (err) {
            App.showToast(err.message, 'error');
        }
    },

    // ── Helpers ────────────────────────────────────────────────────

    formatDateTime(isoString) {
        if (!isoString) return '';
        const d = new Date(isoString);
        return d.toLocaleDateString([], { month: 'short', day: 'numeric' }) +
            ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },

    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    destroy() { },
};
