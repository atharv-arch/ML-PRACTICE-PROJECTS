/**
 * App.js — Main SPA Router and Application Shell Controller.
 *
 * This is the core orchestrator of the single-page application.
 * It manages navigation between views, handles the task modal lifecycle,
 * and provides global utility functions like toast notifications.
 *
 * Architecture:
 *   - Hash-based routing (#dashboard, #tasks, #calendar, etc.)
 *   - Each view is a standalone module with render() and destroy() methods
 *   - Modal is shared across views for creating/editing tasks
 *   - Toast notifications for user feedback on actions
 */

const App = {
    // Currently active view module reference
    currentView: null,

    // Name of the currently active view (matches hash)
    currentViewName: '',

    // ── View Registry ─────────────────────────────────────────────
    // Maps route names to their view modules and display titles.
    // Each entry has:
    //   - view: the module object (must have render() and destroy())
    //   - title: displayed in the top bar when the view is active
    views: {
        dashboard: { view: DashboardView, title: 'Dashboard' },
        tasks: { view: TasksView, title: 'Tasks' },
        calendar: { view: CalendarView, title: 'Calendar' },
        analytics: { view: AnalyticsView, title: 'Analytics' },
        suggestions: { view: SuggestionsView, title: 'AI Suggestions' },
    },

    /**
     * Initialize the application when the DOM is ready.
     *
     * Sets up:
     *   1. Hash change listener for SPA navigation
     *   2. Task modal create/edit functionality
     *   3. Mobile sidebar toggle
     *   4. Initial page rendering based on current URL hash
     */
    init() {
        // Listen for hash changes — this drives SPA navigation
        window.addEventListener('hashchange', () => this.navigate());

        // Wire up the task modal (open, close, submit)
        this.setupModal();

        // Mobile: hamburger menu toggles the sidebar
        document.getElementById('menu-toggle')?.addEventListener('click', () => {
            document.getElementById('sidebar')?.classList.toggle('open');
        });

        // Mobile: close sidebar when a nav link is clicked
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                document.getElementById('sidebar')?.classList.remove('open');
            });
        });

        // "New Task" button in the top bar opens the modal
        document.getElementById('btn-add-task')?.addEventListener('click', () => {
            this.openTaskModal();
        });

        // Render the initial page based on the current URL hash
        this.navigate();
    },

    /**
     * Navigate to the page specified by the URL hash.
     *
     * Flow:
     *   1. Parse the hash to determine which view to show
     *   2. Destroy the previous view (cleanup charts, listeners, etc.)
     *   3. Update the sidebar active state and page title
     *   4. Render the new view into the page container
     *   5. Show a loading spinner while the view loads its data
     */
    async navigate() {
        // Default to 'dashboard' if no hash is present
        const hash = window.location.hash.replace('#', '') || 'dashboard';
        const pageConfig = this.views[hash];

        // If the hash doesn't match any known view, redirect to dashboard
        if (!pageConfig) {
            window.location.hash = '#dashboard';
            return;
        }

        // Cleanup: destroy the previous view to free resources (e.g., Chart.js instances)
        if (this.currentView?.destroy) {
            this.currentView.destroy();
        }

        // Update internal state
        this.currentViewName = hash;
        this.currentView = pageConfig.view;

        // Highlight the active nav link in the sidebar
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.dataset.page === hash);
        });

        // Update the page title in the top bar
        const titleEl = document.getElementById('page-title');
        if (titleEl) titleEl.textContent = pageConfig.title;

        // Render the view: show a spinner first, then load content
        const container = document.getElementById('page-container');
        if (container) {
            // Show loading spinner while view fetches data
            container.innerHTML = '<div class="loading-screen"><div class="spinner"></div></div>';

            try {
                // Each view's render() method fetches data and builds the DOM
                await pageConfig.view.render(container);
            } catch (err) {
                // Show a user-friendly error if the view fails to load
                console.error(`Failed to render ${hash}:`, err);
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">Warning</div>
                        <div class="empty-state-title">Something went wrong</div>
                        <div class="empty-state-desc">${err.message}</div>
                    </div>
                `;
            }
        }
    },

    // ── Modal Management ──────────────────────────────────────────

    /**
     * Set up event listeners for the task create/edit modal.
     *
     * The modal is a shared DOM element (defined in index.html)
     * that is shown/hidden via CSS class toggling. It supports
     * both creating new tasks and editing existing ones.
     */
    setupModal() {
        const overlay = document.getElementById('task-modal-overlay');
        const closeBtn = document.getElementById('modal-close');
        const cancelBtn = document.getElementById('modal-cancel');
        const form = document.getElementById('task-form');

        // Close modal via X button or Cancel button
        closeBtn?.addEventListener('click', () => this.closeTaskModal());
        cancelBtn?.addEventListener('click', () => this.closeTaskModal());

        // Close modal when clicking outside the modal box (on the overlay)
        overlay?.addEventListener('click', (e) => {
            if (e.target === overlay) this.closeTaskModal();
        });

        // Close modal on Escape key press
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closeTaskModal();
        });

        // Handle form submission (create or update task)
        form?.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.submitTask();
        });
    },

    /**
     * Open the task modal for creating or editing a task.
     *
     * @param {Object|null} existingTask - If provided, pre-fills the form
     *   with the task's data for editing. If null, opens a blank form
     *   for creating a new task.
     */
    openTaskModal(existingTask = null) {
        const overlay = document.getElementById('task-modal-overlay');
        const title = document.getElementById('modal-title');
        const submitBtn = document.getElementById('modal-submit');

        if (existingTask) {
            // ── Edit Mode: populate form with existing task data ──
            title.textContent = 'Edit Task';
            submitBtn.textContent = 'Update Task';

            // Fill in all form fields from the task object
            document.getElementById('task-id').value = existingTask.id;
            document.getElementById('task-title').value = existingTask.title;
            document.getElementById('task-description').value = existingTask.description || '';
            document.getElementById('task-category').value = existingTask.category || 'general';
            document.getElementById('task-priority').value = existingTask.priority || 2;
            document.getElementById('task-duration').value = existingTask.duration_minutes || 30;
            document.getElementById('task-reminder').value = existingTask.reminder_minutes_before || 10;

            // Format the assigned time for the datetime-local input
            if (existingTask.assigned_time) {
                const dt = new Date(existingTask.assigned_time);
                const formatted = dt.toISOString().slice(0, 16);  // "YYYY-MM-DDTHH:MM"
                document.getElementById('task-time').value = formatted;
            }
        } else {
            // ── Create Mode: reset form to defaults ──────────────
            title.textContent = 'Add New Task';
            submitBtn.textContent = 'Save Task';
            document.getElementById('task-form').reset();
            document.getElementById('task-id').value = '';  // Clear hidden ID

            // Default the scheduled time to the next full hour
            const now = new Date();
            now.setHours(now.getHours() + 1, 0, 0, 0);
            const formatted = now.toISOString().slice(0, 16);
            document.getElementById('task-time').value = formatted;
        }

        // Show the modal with CSS animation
        overlay?.classList.add('active');

        // Focus the title input for immediate typing
        document.getElementById('task-title')?.focus();
    },

    /**
     * Close the task modal and clear the overlay.
     */
    closeTaskModal() {
        document.getElementById('task-modal-overlay')?.classList.remove('active');
    },

    /**
     * Handle task form submission — create new or update existing.
     *
     * Reads all form values, constructs the API payload, and sends
     * the request. On success, closes the modal and refreshes the
     * current view to show the updated data.
     */
    async submitTask() {
        // Check if we're editing (task ID present) or creating
        const taskId = document.getElementById('task-id').value;

        // Build the task data payload from form inputs
        const taskData = {
            title: document.getElementById('task-title').value.trim(),
            description: document.getElementById('task-description').value.trim(),
            category: document.getElementById('task-category').value,
            priority: parseInt(document.getElementById('task-priority').value),
            duration_minutes: parseInt(document.getElementById('task-duration').value) || 30,
            reminder_minutes_before: parseInt(document.getElementById('task-reminder').value) || 10,
        };

        // Convert the datetime-local value to ISO format for the API
        const timeValue = document.getElementById('task-time').value;
        if (timeValue) {
            taskData.assigned_time = new Date(timeValue).toISOString();
        }

        // Client-side validation: title is required
        if (!taskData.title) {
            this.showToast('Task title is required', 'error');
            return;
        }

        try {
            if (taskId) {
                // Update existing task via PUT
                await api.updateTask(parseInt(taskId), taskData);
                this.showToast('Task updated!', 'success');
            } else {
                // Create new task via POST
                await api.createTask(taskData);
                this.showToast('Task created!', 'success');
            }

            // Close the modal after successful save
            this.closeTaskModal();

            // Refresh the current view to reflect changes
            // Some views have a dedicated loadTasks() method, others need full re-render
            if (this.currentView?.loadTasks) {
                await this.currentView.loadTasks();
            } else if (this.currentView?.render) {
                const container = document.getElementById('page-container');
                if (container) await this.currentView.render(container);
            }
        } catch (err) {
            // Show the API error message to the user
            this.showToast(err.message, 'error');
        }
    },

    // ── Toast Notification System ─────────────────────────────────

    /**
     * Show a temporary notification message (toast).
     *
     * Toasts appear in the bottom-right corner and auto-dismiss
     * after the specified duration. They slide in from the right
     * with a CSS animation.
     *
     * @param {string} message - The message to display
     * @param {string} type    - 'success' | 'error' | 'info' (controls color)
     * @param {number} duration - Auto-dismiss time in milliseconds
     */
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        // Map toast types to icons
        const icons = { success: '[OK]', error: '[X]', info: '[i]' };

        // Create the toast DOM element
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || '[i]'}</span>
            <span class="toast-message">${message}</span>
        `;

        // Append to the container (triggers slide-in animation)
        container.appendChild(toast);

        // Auto-remove after duration with a fade-out transition
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            // Remove from DOM after the animation completes
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },
};

// ── Application Bootstrap ─────────────────────────────────────────────
// Start the app once all DOM content has loaded (scripts, styles, etc.)
document.addEventListener('DOMContentLoaded', () => App.init());
