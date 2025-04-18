// Calendar.js - Advanced calendar functionality for Gestor de Citas
// This script extends the FullCalendar implementation with custom functionality

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a page with a calendar
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;
    
    // Default calendar configuration
    const calendarConfig = {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
        },
        locale: 'es',
        firstDay: 1, // Monday as first day of week
        businessHours: true,
        navLinks: true,
        editable: false,
        dayMaxEvents: true,
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        },
        views: {
            timeGrid: {
                dayMaxEventRows: 6,
                dayMinWidth: 100,
                slotDuration: '00:30:00',
                slotLabelFormat: {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false
                }
            }
        },
        height: 'auto',
        themeSystem: 'bootstrap',
        nowIndicator: true,
        weekNumbers: false,
        buttonText: {
            today: 'Hoy',
            month: 'Mes',
            week: 'Semana',
            day: 'Día',
            list: 'Lista'
        },
        buttonIcons: {
            prev: 'chevron-left',
            next: 'chevron-right'
        },
        allDayText: 'Todo el día',
        noEventsText: 'No hay eventos para mostrar',
        // Custom styling for events
        eventClassNames: function(arg) {
            // Add custom classes based on event status
            const eventStatus = arg.event.extendedProps.status || 'default';
            return [`event-status-${eventStatus}`];
        },
        // For professional calendar view
        eventDidMount: function(info) {
            // Add tooltips to events
            const tooltip = new bootstrap.Tooltip(info.el, {
                title: info.event.title,
                placement: 'top',
                trigger: 'hover',
                container: 'body'
            });
        }
    };
    
    // Initialize different calendars based on page context
    if (window.location.pathname.includes('/professional/calendar')) {
        // Professional's full calendar with appointments
        initializeProfessionalCalendar(calendarEl, calendarConfig);
    } else if (window.location.pathname.includes('/book_appointment')) {
        // Client booking calendar (simplified view)
        initializeBookingCalendar(calendarEl, calendarConfig);
    } else if (window.location.pathname.includes('/professional_profile')) {
        // Read-only profile calendar (simplified)
        initializeProfileCalendar(calendarEl, calendarConfig);
    } else {
        // Default calendar
        const calendar = new FullCalendar.Calendar(calendarEl, calendarConfig);
        calendar.render();
    }
});

/**
 * Initialize the professional's full calendar with all appointments
 * @param {HTMLElement} calendarEl - Calendar container element
 * @param {Object} baseConfig - Base calendar configuration
 */
function initializeProfessionalCalendar(calendarEl, baseConfig) {
    // Get the API endpoint from the data attribute or default to the standard endpoint
    const eventsUrl = calendarEl.dataset.eventsUrl || "/professional/api/appointments";
    
    // Extend the base configuration
    const professionalConfig = {
        ...baseConfig,
        initialView: 'timeGridWeek',
        events: eventsUrl,
        eventClick: function(info) {
            showAppointmentDetails(info.event);
        },
        dateClick: function(info) {
            // Optional: Add functionality for clicking on dates
            console.log('Clicked on: ' + info.dateStr);
        },
        // Load business hours from schedules
        businessHours: window.businessHours || baseConfig.businessHours
    };
    
    // Create and render calendar
    const calendar = new FullCalendar.Calendar(calendarEl, professionalConfig);
    calendar.render();
    
    // Add event listener for the refresh button if it exists
    const refreshBtn = document.getElementById('refresh-calendar');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            calendar.refetchEvents();
        });
    }
    
    // Add event listeners for filter buttons if they exist
    const filterButtons = document.querySelectorAll('.calendar-filter-btn');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all filter buttons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Get filter value
            const filterValue = this.dataset.filter;
            
            // Apply filtering
            if (filterValue === 'all') {
                calendar.getEvents().forEach(event => event.setProp('display', 'auto'));
            } else {
                calendar.getEvents().forEach(event => {
                    const eventStatus = event.extendedProps.status;
                    event.setProp('display', eventStatus === filterValue ? 'auto' : 'none');
                });
            }
        });
    });
    
    // Add window resize handler to adjust calendar
    window.addEventListener('resize', function() {
        calendar.updateSize();
    });
    
    return calendar;
}

/**
 * Initialize a simplified booking calendar for clients
 * @param {HTMLElement} calendarEl - Calendar container element
 * @param {Object} baseConfig - Base calendar configuration
 */
function initializeBookingCalendar(calendarEl, baseConfig) {
    // Simplified configuration for booking view
    const bookingConfig = {
        ...baseConfig,
        initialView: 'dayGridWeek',
        selectable: true,
        unselectAuto: false,
        select: function(info) {
            // Handle date selection for booking
            selectBookingDate(info.startStr);
        },
        dateClick: function(info) {
            // Handle date click for booking
            selectBookingDate(info.dateStr);
        },
        // Disable days in the past
        validRange: {
            start: new Date()
        }
    };
    
    // Create and render calendar
    const calendar = new FullCalendar.Calendar(calendarEl, bookingConfig);
    calendar.render();
    
    return calendar;
}

/**
 * Initialize a read-only calendar for professional profile
 * @param {HTMLElement} calendarEl - Calendar container element
 * @param {Object} baseConfig - Base calendar configuration
 */
function initializeProfileCalendar(calendarEl, baseConfig) {
    // Simplified configuration for profile view
    const profileConfig = {
        ...baseConfig,
        initialView: 'dayGridWeek',
        headerToolbar: {
            left: '',
            center: 'title',
            right: ''
        },
        height: 'auto',
        contentHeight: 350,
        dayMaxEvents: 0, // Hide events, only show business hours
        // Disable interaction
        selectable: false,
        navLinks: false,
        // Only show next 2 weeks
        duration: { weeks: 2 }
    };
    
    // Create and render calendar
    const calendar = new FullCalendar.Calendar(calendarEl, profileConfig);
    calendar.render();
    
    return calendar;
}

/**
 * Handle date selection for booking appointments
 * @param {string} dateStr - Selected date in ISO format
 */
function selectBookingDate(dateStr) {
    // Update the date input in the booking form
    const dateInput = document.getElementById('date');
    if (dateInput) {
        dateInput.value = dateStr.split('T')[0]; // Extract just the date part
        
        // Trigger change event to update available slots
        const event = new Event('change');
        dateInput.dispatchEvent(event);
        
        // If there's a tab for this date, activate it
        const dateTab = document.querySelector(`[data-date="${dateStr.split('T')[0]}"]`);
        if (dateTab) {
            const tabInstance = new bootstrap.Tab(dateTab);
            tabInstance.show();
        }
    }
}

/**
 * Display appointment details in modal
 * @param {Object} event - FullCalendar event object
 */
function showAppointmentDetails(event) {
    // Get modal elements
    const modal = document.getElementById('appointmentModal');
    if (!modal) return;
    
    const startDate = new Date(event.start);
    const endDate = new Date(event.end);
    
    // Format date and time
    const dateOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const formattedDate = startDate.toLocaleDateString('es-ES', dateOptions);
    const formattedTime = `${startDate.toLocaleTimeString('es-ES', {hour: '2-digit', minute:'2-digit', hour12: false})} - 
                           ${endDate.toLocaleTimeString('es-ES', {hour: '2-digit', minute:'2-digit', hour12: false})}`;
    
    // Set modal content
    document.getElementById('modalClientName').textContent = event.extendedProps.clientName || 'No disponible';
    document.getElementById('modalDate').textContent = formattedDate;
    document.getElementById('modalTime').textContent = formattedTime;
    
    // Set status with badge
    let statusHtml = '';
    const status = event.extendedProps.status;
    const statusMap = {
        'pending': { text: 'Pendiente', class: 'bg-warning' },
        'confirmed': { text: 'Confirmada', class: 'bg-success' },
        'cancelled': { text: 'Cancelada', class: 'bg-danger' },
        'completed': { text: 'Completada', class: 'bg-info' }
    };
    
    const statusInfo = statusMap[status] || { text: 'Desconocido', class: 'bg-secondary' };
    statusHtml = `<span class="badge ${statusInfo.class}">${statusInfo.text}</span>`;
    
    document.getElementById('modalStatus').innerHTML = statusHtml;
    document.getElementById('modalNotes').textContent = event.extendedProps.notes || 'Sin notas';
    
    // Set edit link
    const editLink = document.getElementById('modalEditLink');
    if (editLink) {
        const appointmentId = event.id;
        // Update the href to point to the correct edit page
        const editUrl = `/professional/update_appointment/${appointmentId}`;
        editLink.href = editUrl;
    }
    
    // Show modal
    const appointmentModal = new bootstrap.Modal(modal);
    appointmentModal.show();
}

/**
 * Utility function to format a date for display
 * @param {Date} date - Date object
 * @param {boolean} includeTime - Whether to include time
 * @returns {string} Formatted date string
 */
function formatDate(date, includeTime = false) {
    const options = { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric'
    };
    
    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
        options.hour12 = false;
    }
    
    return date.toLocaleDateString('es-ES', options);
}

/**
 * Update available time slots based on selected date
 * This function can be called when date input changes
 * @param {string} dateStr - Selected date in ISO format
 * @param {number} professionalId - Professional ID
 */
function updateAvailableTimeSlots(dateStr, professionalId) {
    // This would typically involve an AJAX call to get available slots
    // For now, we'll just show a loading indicator
    const slotsContainer = document.querySelector('.time-slots-container');
    if (!slotsContainer) return;
    
    slotsContainer.innerHTML = '<p class="text-center"><i class="fas fa-spinner fa-spin"></i> Cargando horarios disponibles...</p>';
    
    // In a real implementation, you would fetch the data from the server
    // fetch(`/api/available-slots?date=${dateStr}&professional_id=${professionalId}`)
    //   .then(response => response.json())
    //   .then(data => {
    //     // Update the UI with the available slots
    //   })
    //   .catch(error => {
    //     console.error('Error fetching available slots:', error);
    //     slotsContainer.innerHTML = '<p class="text-center text-danger">Error al cargar horarios disponibles</p>';
    //   });
}
