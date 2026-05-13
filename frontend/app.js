let token = localStorage.getItem('token');
let isAdmin = false;
let isDoctor = false;

const API_URL = 'http://localhost:8000';
const content = () => document.getElementById('content-area');

function showToast(message, type = 'info', duration = 4000) {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    toast.innerHTML = `
        <div class="toast-message">${escapeHtml(message)}</div>
        <button class="toast-close" onclick="this.parentElement.remove()">x</button>
    `;

    toastContainer.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

async function api(path, options = {}) {
    const headers = options.headers || {};
    if (token) headers.Authorization = `Bearer ${token}`;
    if (options.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';

    const response = await fetch(`${API_URL}${path}`, { ...options, headers });
    let data = null;
    const text = await response.text();
    if (text) {
        try { data = JSON.parse(text); } catch { data = text; }
    }

    if (!response.ok) {
        const message = data?.detail || data || 'Request failed';
        throw new Error(Array.isArray(message) ? message.map(item => item.msg).join('\n') : message);
    }
    return data;
}

async function login() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    try {
        const data = await api('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        token = data.access_token;
        localStorage.setItem('token', token);
        await checkUserRole();
        showApp();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function register() {
    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;

    try {
        await api('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });
        showToast('Registration successful. Please login.', 'success');
        showLogin();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function checkUserRole() {
    try {
        const user = await api('/users/me');
        isAdmin = Boolean(user.is_admin);
        isDoctor = Boolean(user.is_doctor);
        document.getElementById('admin-menu').style.display = isAdmin ? 'block' : 'none';
        document.getElementById('doctor-menu').style.display = isDoctor ? 'block' : 'none';
        document.getElementById('logoutBtn').style.display = 'inline-block';
    } catch (error) {
        logout();
    }
}

function logout() {
    token = null;
    isAdmin = false;
    isDoctor = false;
    localStorage.removeItem('token');
    document.getElementById('logoutBtn').style.display = 'none';
    showLogin();
}

document.getElementById('logoutBtn').addEventListener('click', logout);

function showLoading() {
    const container = content();
    container.innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner"></i>
            <h3>Loading...</h3>
        </div>
    `;
}

async function showDoctors() {
    showLoading();
    try {
        const doctors = await api('/doctors/');
        const container = content();
        container.innerHTML = '<h2><i class="fas fa-user-md"></i> Our Doctors</h2>';

        if (doctors.length === 0) {
            container.innerHTML += `
                <div class="empty-state">
                    <i class="fas fa-user-md"></i>
                    <h3>No doctors available</h3>
                </div>
            `;
            return;
        }

        const grid = document.createElement('div');
        grid.className = 'products-grid';

        doctors.forEach(doctor => {
            const card = document.createElement('div');
            card.className = 'product-card';
            card.innerHTML = `
                <div class="product-image" style="background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);">
                    <i class="fas fa-user-md" style="font-size: 4rem; color: #0284c7;"></i>
                </div>
                <div class="product-info">
                    <h3>Dr. ${escapeHtml(doctor.first_name)} ${escapeHtml(doctor.last_name)}</h3>
                    <p class="product-description">
                        <i class="fas fa-stethoscope"></i> ${escapeHtml(doctor.specialization)}
                    </p>
                    <p style="color: var(--text-secondary); font-size: 14px;">
                        <i class="fas fa-phone"></i> ${escapeHtml(doctor.phone || 'N/A')}
                    </p>
                    <div class="product-actions" style="margin-top: 1rem;">
                        <button onclick="bookAppointment(${doctor.id}, '${escapeHtml(doctor.first_name)} ${escapeHtml(doctor.last_name)}', '${escapeHtml(doctor.specialization)}')" class="btn btn-primary">
                            <i class="fas fa-calendar-plus"></i> Book Appointment
                        </button>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });

        container.appendChild(grid);
    } catch (error) {
        content().innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Error loading doctors</h3>
                <p>${escapeHtml(error.message)}</p>
            </div>
        `;
    }
}

let bookingDoctorId = null;
let bookingDoctorName = '';

function bookAppointment(doctorId, doctorName, specialization) {
    if (!token) {
        showToast('Please login first.', 'warning');
        return;
    }
    bookingDoctorId = doctorId;
    bookingDoctorName = doctorName;

    const container = content();
    container.innerHTML = `
        <h2><i class="fas fa-calendar-plus"></i> Book Appointment</h2>
        <p style="margin: 1rem 0; color: var(--text-secondary);">
            Booking with <strong>Dr. ${escapeHtml(doctorName)}</strong> (${escapeHtml(specialization)})
        </p>
        <div class="admin-form">
            <label>Appointment Date & Time:</label>
            <input id="appointment-date" type="datetime-local" style="margin: 8px 0; padding: 10px; border: 1px solid var(--border-color); border-radius: var(--border-radius); width: 100%;">
            <label>Notes (optional):</label>
            <textarea id="appointment-notes" placeholder="Any specific concerns..." style="margin: 8px 0;"></textarea>
            <button onclick="submitAppointment()" class="btn btn-success" style="margin-top: 1rem;">
                <i class="fas fa-check"></i> Confirm Booking
            </button>
        </div>
    `;
}

async function submitAppointment() {
    const dateInput = document.getElementById('appointment-date').value;
    const notes = document.getElementById('appointment-notes').value;

    if (!dateInput) {
        showToast('Please select a date and time.', 'warning');
        return;
    }

    const appointmentDate = new Date(dateInput).toISOString();

    try {
        await api('/appointments/', {
            method: 'POST',
            body: JSON.stringify({
                doctor_id: bookingDoctorId,
                appointment_date: appointmentDate,
                notes: notes || null
            })
        });
        showToast(`Appointment booked with Dr. ${bookingDoctorName}.`, 'success');
        showAppointments();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function showAppointments() {
    showLoading();
    try {
        const appointments = await api('/appointments/');
        const container = content();
        container.innerHTML = '<h2><i class="fas fa-calendar-check"></i> My Appointments</h2>';

        if (appointments.length === 0) {
            container.innerHTML += `
                <div class="empty-state">
                    <i class="fas fa-calendar"></i>
                    <h3>No appointments</h3>
                    <p>Book an appointment with one of our doctors.</p>
                    <button onclick="showDoctors()" class="btn btn-primary" style="margin-top: 1rem;">
                        <i class="fas fa-user-md"></i> Browse Doctors
                    </button>
                </div>
            `;
            return;
        }

        appointments.forEach(appt => {
            const card = document.createElement('div');
            card.className = 'order-item';
            card.style.cssText = `
                background: var(--surface-color);
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius);
                padding: 1.5rem;
                margin-bottom: 1rem;
            `;

            const statusClass = appt.status === 'scheduled' ? 'status-pending' :
                               appt.status === 'completed' ? 'status-completed' : 'status-cancelled';

            const dateStr = new Date(appt.appointment_date).toLocaleString();

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                    <div>
                        <h3 style="margin: 0 0 8px 0; color: var(--text-primary);">Appointment #${appt.id}</h3>
                        <div style="display: flex; gap: 1rem; align-items: center;">
                            <span class="status-badge ${statusClass}">${appt.status}</span>
                        </div>
                    </div>
                </div>
                <div style="margin-bottom: 1rem;">
                    <p><i class="fas fa-user-md"></i> <strong>Doctor:</strong> Dr. ${escapeHtml(appt.doctor_name || 'N/A')}</p>
                    <p><i class="fas fa-stethoscope"></i> <strong>Specialization:</strong> ${escapeHtml(appt.doctor_specialization || 'N/A')}</p>
                    <p><i class="fas fa-clock"></i> <strong>Date:</strong> ${escapeHtml(dateStr)}</p>
                    ${appt.notes ? `<p><i class="fas fa-notes"></i> <strong>Notes:</strong> ${escapeHtml(appt.notes)}</p>` : ''}
                </div>
                ${appt.status === 'scheduled' ? `
                    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                        <button onclick="cancelAppointment(${appt.id})" class="btn btn-outline">
                            <i class="fas fa-times"></i> Cancel Appointment
                        </button>
                    </div>
                ` : ''}
            `;
            container.appendChild(card);
        });
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function cancelAppointment(appointmentId) {
    try {
        await api(`/appointments/${appointmentId}/cancel`, { method: 'POST' });
        showToast('Appointment cancelled.', 'success');
        showAppointments();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function showDoctorSchedule() {
    showLoading();
    try {
        const appointments = await api('/appointments/');
        const container = content();
        container.innerHTML = '<h2><i class="fas fa-clock"></i> My Schedule</h2>';

        if (appointments.length === 0) {
            container.innerHTML += `
                <div class="empty-state">
                    <i class="fas fa-calendar"></i>
                    <h3>No appointments in your schedule</h3>
                </div>
            `;
            return;
        }

        appointments.forEach(appt => {
            const card = document.createElement('div');
            card.className = 'order-item';
            card.style.cssText = `
                background: var(--surface-color);
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius);
                padding: 1.5rem;
                margin-bottom: 1rem;
            `;

            const statusClass = appt.status === 'scheduled' ? 'status-pending' :
                               appt.status === 'completed' ? 'status-completed' : 'status-cancelled';
            const dateStr = new Date(appt.appointment_date).toLocaleString();

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                    <div>
                        <h3 style="margin: 0 0 8px 0; color: var(--text-primary);">Appointment #${appt.id}</h3>
                        <div style="display: flex; gap: 1rem; align-items: center;">
                            <span class="status-badge ${statusClass}">${appt.status}</span>
                        </div>
                    </div>
                </div>
                <div style="margin-bottom: 1rem;">
                    <p><i class="fas fa-user"></i> <strong>Patient:</strong> ${escapeHtml(appt.patient_name || 'N/A')}</p>
                    <p><i class="fas fa-clock"></i> <strong>Date:</strong> ${escapeHtml(dateStr)}</p>
                    ${appt.notes ? `<p><i class="fas fa-notes"></i> <strong>Notes:</strong> ${escapeHtml(appt.notes)}</p>` : ''}
                </div>
                ${appt.status === 'scheduled' ? `
                    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                        <div style="display: flex; gap: 8px;">
                            <select id="status-${appt.id}" style="padding: 8px; border: 1px solid var(--border-color); border-radius: var(--border-radius);">
                                <option value="scheduled">Scheduled</option>
                                <option value="completed">Completed</option>
                                <option value="cancelled">Cancelled</option>
                            </select>
                            <button onclick="updateAppointmentStatus(${appt.id})" class="btn btn-primary">
                                <i class="fas fa-save"></i> Update
                            </button>
                        </div>
                    </div>
                ` : ''}
            `;
            container.appendChild(card);
        });
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function updateAppointmentStatus(appointmentId) {
    try {
        const status = document.getElementById(`status-${appointmentId}`).value;
        await api(`/appointments/${appointmentId}/status?status=${status}`, { method: 'PUT' });
        showToast('Status updated.', 'success');
        showDoctorSchedule();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function showLogin() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('app-content').style.display = 'none';
}

function showRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
    document.getElementById('app-content').style.display = 'none';
}

function showApp() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('app-content').style.display = 'block';
    showDoctors();
}

function requireAdmin() {
    if (!isAdmin) {
        showToast('Admin privileges required.', 'warning');
        return false;
    }
    return true;
}

async function showAddDoctor() {
    if (!requireAdmin()) return;
    content().innerHTML = `
        <h2><i class="fas fa-user-md"></i> Add Doctor</h2>
        <div class="admin-form">
            <input id="doc-username" placeholder="Username">
            <input id="doc-email" type="email" placeholder="Email">
            <input id="doc-password" type="password" placeholder="Password">
            <input id="doc-firstname" placeholder="First Name">
            <input id="doc-lastname" placeholder="Last Name">
            <input id="doc-specialization" placeholder="Specialization">
            <input id="doc-phone" placeholder="Phone">
            <button onclick="submitDoctor()" class="btn btn-success"><i class="fas fa-plus"></i> Create Doctor</button>
        </div>
    `;
}

async function submitDoctor() {
    try {
        await api('/doctors/', {
            method: 'POST',
            body: JSON.stringify({
                username: document.getElementById('doc-username').value,
                email: document.getElementById('doc-email').value,
                password: document.getElementById('doc-password').value,
                first_name: document.getElementById('doc-firstname').value,
                last_name: document.getElementById('doc-lastname').value,
                specialization: document.getElementById('doc-specialization').value,
                phone: document.getElementById('doc-phone').value || null,
            })
        });
        showToast('Doctor created.', 'success');
        showDoctors();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function showAddPatient() {
    if (!requireAdmin()) return;
    content().innerHTML = `
        <h2><i class="fas fa-user"></i> Add Patient</h2>
        <div class="admin-form">
            <input id="pat-username" placeholder="Username">
            <input id="pat-email" type="email" placeholder="Email">
            <input id="pat-password" type="password" placeholder="Password">
            <input id="pat-firstname" placeholder="First Name">
            <input id="pat-lastname" placeholder="Last Name">
            <input id="pat-phone" placeholder="Phone">
            <button onclick="submitPatient()" class="btn btn-success"><i class="fas fa-plus"></i> Create Patient</button>
        </div>
    `;
}

async function submitPatient() {
    try {
        await api('/patients/', {
            method: 'POST',
            body: JSON.stringify({
                username: document.getElementById('pat-username').value,
                email: document.getElementById('pat-email').value,
                password: document.getElementById('pat-password').value,
                first_name: document.getElementById('pat-firstname').value,
                last_name: document.getElementById('pat-lastname').value,
                phone: document.getElementById('pat-phone').value || null,
            })
        });
        showToast('Patient created.', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function showAllAppointments() {
    if (!requireAdmin()) return;
    try {
        const appointments = await api('/appointments/all');
        const container = content();
        container.innerHTML = '<h2><i class="fas fa-list"></i> All Appointments</h2>';

        if (appointments.length === 0) {
            container.innerHTML += `
                <div class="empty-state">
                    <i class="fas fa-calendar"></i>
                    <h3>No appointments</h3>
                </div>
            `;
            return;
        }

        appointments.forEach(appt => {
            const card = document.createElement('div');
            card.className = 'order-item';
            card.style.cssText = `
                background: var(--surface-color);
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius);
                padding: 1.5rem;
                margin-bottom: 1rem;
            `;

            const statusClass = appt.status === 'scheduled' ? 'status-pending' :
                               appt.status === 'completed' ? 'status-completed' : 'status-cancelled';
            const dateStr = new Date(appt.appointment_date).toLocaleString();

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h3 style="margin: 0 0 8px 0;">Appointment #${appt.id}</h3>
                        <p><strong>Patient:</strong> ${escapeHtml(appt.patient_name || 'N/A')}</p>
                        <p><strong>Doctor:</strong> Dr. ${escapeHtml(appt.doctor_name || 'N/A')}</p>
                        <p><strong>Date:</strong> ${escapeHtml(dateStr)}</p>
                        <span class="status-badge ${statusClass}">${appt.status}</span>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        showToast(error.message, 'error');
    }
}

if (token) {
    checkUserRole().then(showApp).catch(showLogin);
} else {
    showLogin();
}
