/**
 * Calendar View — Monthly calendar grid showing tasks per day.
 *
 * Features:
 *   - Month navigation (prev/next)
 *   - Color-coded dots for task statuses
 *   - Click a day to see tasks for that date
 *   - Today highlighting
 */

const CalendarView = {
    currentDate: new Date(),

    async render(container) {
        container.innerHTML = `
            <div class="fade-in">
                <div class="calendar-header">
                    <div class="calendar-nav">
                        <button class="calendar-nav-btn" id="cal-prev" aria-label="Previous month">◀</button>
                        <span class="calendar-month-label" id="cal-month-label"></span>
                        <button class="calendar-nav-btn" id="cal-next" aria-label="Next month">▶</button>
                    </div>
                    <button class="btn btn-secondary btn-sm" id="cal-today-btn">Today</button>
                </div>
                <div class="card">
                    <div class="calendar-grid" id="calendar-grid"></div>
                </div>
                <div class="card" style="margin-top: 20px;" id="day-detail" style="display:none;">
                    <div class="card-header">
                        <div class="card-title" id="day-detail-title">Select a day</div>
                    </div>
                    <div class="task-list" id="day-tasks"></div>
                </div>
            </div>
        `;

        this.bindEvents();
        await this.renderCalendar();
    },

    bindEvents() {
        document.getElementById('cal-prev')?.addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() - 1);
            this.renderCalendar();
        });
        document.getElementById('cal-next')?.addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() + 1);
            this.renderCalendar();
        });
        document.getElementById('cal-today-btn')?.addEventListener('click', () => {
            this.currentDate = new Date();
            this.renderCalendar();
        });
    },

    async renderCalendar() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();

        // Update month label
        const monthLabel = document.getElementById('cal-month-label');
        if (monthLabel) {
            monthLabel.textContent = new Date(year, month).toLocaleDateString('en-US', {
                month: 'long', year: 'numeric',
            });
        }

        // Get all tasks for this month
        let tasks = [];
        try {
            const data = await api.listTasks({ per_page: 100 });
            tasks = data.tasks || [];
        } catch (err) {
            console.error('Failed to load tasks for calendar:', err);
        }

        // Group tasks by date
        const tasksByDate = {};
        tasks.forEach(task => {
            if (task.assigned_time) {
                const dateKey = task.assigned_time.split('T')[0];
                if (!tasksByDate[dateKey]) tasksByDate[dateKey] = [];
                tasksByDate[dateKey].push(task);
            }
        });

        // Build calendar grid
        const grid = document.getElementById('calendar-grid');
        if (!grid) return;

        const today = new Date();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDow = firstDay.getDay(); // 0=Sun
        const daysInMonth = lastDay.getDate();

        // Day headers
        let html = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            .map(d => `<div class="calendar-day-header">${d}</div>`)
            .join('');

        // Previous month padding
        const prevMonthLast = new Date(year, month, 0).getDate();
        for (let i = startDow - 1; i >= 0; i--) {
            const day = prevMonthLast - i;
            html += `<div class="calendar-day other-month"><span class="day-number">${day}</span></div>`;
        }

        // Current month days
        for (let day = 1; day <= daysInMonth; day++) {
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const isToday = today.getFullYear() === year && today.getMonth() === month && today.getDate() === day;
            const dayTasks = tasksByDate[dateStr] || [];

            const dots = dayTasks.slice(0, 5).map(t => {
                const dotClass = t.status === 'completed' ? 'completed' :
                    t.status === 'missed' ? 'missed' : 'pending';
                return `<span class="day-dot ${dotClass}"></span>`;
            }).join('');

            html += `
                <div class="calendar-day ${isToday ? 'today' : ''}"
                     onclick="CalendarView.showDayDetail('${dateStr}')"
                     title="${dayTasks.length} tasks">
                    <span class="day-number">${day}</span>
                    <div class="day-dots">${dots}</div>
                </div>
            `;
        }

        // Next month padding
        const totalCells = startDow + daysInMonth;
        const remaining = (7 - (totalCells % 7)) % 7;
        for (let i = 1; i <= remaining; i++) {
            html += `<div class="calendar-day other-month"><span class="day-number">${i}</span></div>`;
        }

        grid.innerHTML = html;
    },

    /** Show task details for a selected day */
    async showDayDetail(dateStr) {
        const detailCard = document.getElementById('day-detail');
        const titleEl = document.getElementById('day-detail-title');
        const listEl = document.getElementById('day-tasks');
        if (!detailCard || !titleEl || !listEl) return;

        detailCard.style.display = 'block';
        const dateObj = new Date(dateStr + 'T00:00:00');
        titleEl.textContent = dateObj.toLocaleDateString('en-US', {
            weekday: 'long', month: 'long', day: 'numeric',
        });

        try {
            const data = await api.listTasks({ date: dateStr, per_page: 50 });
            const tasks = data.tasks || [];

            if (tasks.length === 0) {
                listEl.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📅</div>
                        <div class="empty-state-title">No tasks on this day</div>
                    </div>
                `;
                return;
            }

            listEl.innerHTML = tasks.map(task => `
                <div class="task-item ${task.status === 'completed' ? 'completed' : ''}">
                    <div class="task-check" onclick="TasksView.toggleTask(${task.id}, '${task.status}')">
                        ${task.status === 'completed' ? '✓' : ''}
                    </div>
                    <div class="task-item-content">
                        <div class="task-item-title">${this.escapeHtml(task.title)}</div>
                        <div class="task-item-meta">
                            <span class="task-badge category">${task.category}</span>
                            <span class="task-badge priority-${task.priority}">P${task.priority}</span>
                            <span>⏱ ${task.duration_minutes}min</span>
                            ${task.assigned_time ? `<span>⏰ ${new Date(task.assigned_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>` : ''}
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (err) {
            listEl.innerHTML = '<p style="color:var(--danger)">Failed to load tasks</p>';
        }
    },

    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    destroy() { },
};
