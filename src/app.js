const API_BASE = "https://mmrq6ebalh.execute-api.us-east-1.amazonaws.com";

// Helper to escape HTML characters securely
function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

let loadedEvents = [];

async function loadEvents() {
  const container = document.getElementById("events-list");
  const countBadge = document.getElementById("events-count");

  try {
    const response = await fetch(`${API_BASE}/events`);
    const data = await response.json();

    if (!data.events || data.events.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <span class="empty-icon">📅</span>
          <p>No events scheduled at the moment. Check back soon!</p>
        </div>
      `;
      countBadge.textContent = "0";
      loadedEvents = [];
      return;
    }

    loadedEvents = data.events;
    countBadge.textContent = data.events.length;
    container.innerHTML = data.events
      .map((event) => {
        const name = escapeHtml(event.name);
        const date = escapeHtml(event.date || "Date to be announced");
        const location = escapeHtml(event.location || "Location pending");
        const capacity = event.capacity ? `${event.capacity} seats` : "Unlimited capacity";

        return `
          <div class="event-card">
            <div class="card-details">
              <span class="card-tag">Upcoming</span>
              <h3 class="card-title">${name}</h3>
              <div class="card-meta">
                <div class="meta-item">
                  <span class="meta-icon">📅</span>
                  <span>${date}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-icon">📍</span>
                  <span>${location}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-icon">👥</span>
                  <span>${capacity}</span>
                </div>
              </div>
            </div>
            <div class="card-actions">
              <button 
                commandfor="register-dialog" 
                command="show-modal" 
                data-event-id="${event.event_id}" 
                data-event-name="${name}" 
                class="btn-register"
              >
                Get Ticket
              </button>
            </div>
          </div>
        `;
      })
      .join("");
  } catch (error) {
    container.innerHTML = `
      <div class="error-state">
        <span class="error-icon">⚠️</span>
        <p>Failed to load upcoming events: ${escapeHtml(error.message)}</p>
        <button onclick="loadEvents()" class="btn-retry">Retry</button>
      </div>
    `;
    countBadge.textContent = "!";
  }
}

async function register() {
  const eventId = document.getElementById("reg-event-id").value.trim();
  const name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const messageBox = document.getElementById("reg-msg");
  const submitBtn = document.querySelector("#reg-form button[type='submit']");

  messageBox.textContent = "";
  messageBox.className = "message";

  if (!eventId || !name || !email) {
    messageBox.textContent = "Please fill in all fields before registering.";
    messageBox.classList.add("err");
    return;
  }

  submitBtn.disabled = true;
  const originalText = submitBtn.textContent;
  submitBtn.textContent = "Securing ticket...";

  try {
    const response = await fetch(`${API_BASE}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event_id: eventId, name, email })
    });

    const data = await response.json();

    if (response.ok) {
      messageBox.innerText = `Registration successful!\nConfirmation ID: ${data.registration_id}`;
      messageBox.classList.add("ok");
      document.getElementById("reg-form").reset();

      // Auto-refresh lookup if looking up registrations for this email
      const lookupEmail = document.getElementById("lookup-email").value.trim();
      if (lookupEmail.toLowerCase() === email.toLowerCase()) {
        lookup();
      }

      // Close modal gracefully after success
      setTimeout(() => {
        const dialog = document.getElementById("register-dialog");
        if (dialog.open) {
          dialog.close();
        }
      }, 2500);
    } else {
      messageBox.textContent = `Failed: ${data.error || "Unknown error"}`;
      messageBox.classList.add("err");
    }
  } catch (error) {
    messageBox.textContent = `Request failed: ${error.message}`;
    messageBox.classList.add("err");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = originalText;
  }
}

async function lookup() {
  const email = document.getElementById("lookup-email").value.trim();
  const container = document.getElementById("lookup-results");

  if (!email) {
    container.innerHTML = `
      <div class="empty-state">
        <p>Please enter an email address to look up your tickets.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <span>Retrieving tickets...</span>
    </div>
  `;

  try {
    const response = await fetch(`${API_BASE}/registrations/${encodeURIComponent(email)}`);
    const data = await response.json();

    if (!data.registrations || data.registrations.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <span class="empty-icon">🎟️</span>
          <p>No active registrations found for "${escapeHtml(email)}".</p>
        </div>
      `;
      return;
    }

    container.innerHTML = data.registrations
      .map((registration) => {
        const status = registration.status || "confirmed";
        const dateStr = registration.registered_at 
          ? new Date(registration.registered_at).toLocaleDateString(undefined, { 
              month: 'short', day: 'numeric', year: 'numeric' 
            }) 
          : "N/A";

        // Find the event name from the loadedEvents array
        const matchedEvent = loadedEvents.find((e) => String(e.event_id) === String(registration.event_id));
        const eventName = matchedEvent ? matchedEvent.name : `Event #${registration.event_id}`;

        return `
          <div class="ticket-stub">
            <div class="ticket-header">
              <span class="ticket-status ${status.toLowerCase()}">${status}</span>
              <span class="ticket-date">${dateStr}</span>
            </div>
            <div class="ticket-body">
              <span class="ticket-label">Event</span>
              <strong class="ticket-event-id">${escapeHtml(eventName)}</strong>
              <div class="ticket-id-box">
                <span class="ticket-label">Pass ID</span>
                <code class="ticket-code">${escapeHtml(registration.registration_id)}</code>
              </div>
            </div>
            <div class="ticket-footer">
              <button class="btn-cancel" onclick="cancelReg('${registration.registration_id}', '${escapeHtml(email)}')">
                Cancel Ticket
              </button>
            </div>
          </div>
        `;
      })
      .join("");
  } catch (error) {
    container.innerHTML = `
      <div class="error-state">
        <span class="error-icon">⚠️</span>
        <p>Failed to retrieve tickets: ${escapeHtml(error.message)}</p>
      </div>
    `;
  }
}

async function cancelReg(registrationId, email) {
  if (!confirm("Are you sure you want to cancel this event ticket?")) {
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/registration/${encodeURIComponent(registrationId)}`, {
      method: "DELETE"
    });

    if (response.ok) {
      lookup();
    } else {
      const data = await response.json();
      alert(`Cancel failed: ${data.error || "Unknown error"}`);
    }
  } catch (error) {
    alert(`Request failed: ${error.message}`);
  }
}

// Setup Invoker Commands & Fallbacks
window.addEventListener("DOMContentLoaded", () => {
  loadEvents();

  const dialog = document.getElementById("register-dialog");

  if (dialog) {
    // Intercept show-modal invoker command on the dialog
    dialog.addEventListener("command", (event) => {
      if (event.command === "show-modal") {
        const button = event.source;
        const eventId = button.getAttribute("data-event-id");
        const eventName = button.getAttribute("data-event-name");

        document.getElementById("reg-event-id").value = eventId;
        document.getElementById("modal-event-name").textContent = eventName;

        // Reset state
        document.getElementById("reg-form").reset();
        const messageBox = document.getElementById("reg-msg");
        messageBox.textContent = "";
        messageBox.className = "message";
      }
    });

    // Fallback for click backdrop light-dismiss if closedby is unsupported
    if (!('closedBy' in HTMLDialogElement.prototype)) {
      dialog.addEventListener('click', (event) => {
        if (event.target !== dialog) return;

        const rect = dialog.getBoundingClientRect();
        const isDialogContent = (
          rect.top <= event.clientY &&
          event.clientY <= rect.top + rect.height &&
          rect.left <= event.clientX &&
          event.clientX <= rect.left + rect.width
        );

        if (isDialogContent) return;
        dialog.close();
      });
    }
  }

  // Fallback for browsers lacking Invoker Commands
  if (!('commandForElement' in HTMLButtonElement.prototype)) {
    document.addEventListener('click', (event) => {
      const button = event.composedPath().find((el) => el.matches?.("button[commandfor]"));
      if (!button) return;

      const target = document.getElementById(button.getAttribute('commandfor'));
      const command = button.getAttribute('command');

      if (target && command) {
        if (command === 'show-modal' && typeof target.showModal === 'function') {
          target.showModal();
          const cmdEvent = new CustomEvent('command', {
            bubbles: false,
            cancelable: true
          });
          cmdEvent.command = command;
          cmdEvent.source = button;
          target.dispatchEvent(cmdEvent);
        } else if (command === 'close' && typeof target.close === 'function') {
          target.close();
          const cmdEvent = new CustomEvent('command', {
            bubbles: false,
            cancelable: true
          });
          cmdEvent.command = command;
          cmdEvent.source = button;
          target.dispatchEvent(cmdEvent);
        }
      }
    });
  }
});
