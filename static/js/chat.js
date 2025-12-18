// chat.js - now sends a persistent session_id and handles dialog flows
document.addEventListener('DOMContentLoaded', () => {
  // ensure session id stored in localStorage
  let sessionId = localStorage.getItem('chat_session_id');
  if (!sessionId) {
    sessionId = 's_' + Math.random().toString(36).slice(2,10);
    localStorage.setItem('chat_session_id', sessionId);
  }

  const toggle = document.getElementById('chatToggle');
  const box = document.getElementById('chatBox');
  const closeBtn = document.getElementById('chatClose');
  const sendBtn = document.getElementById('chatSend');
  const input = document.getElementById('chatInput');
  const body = document.getElementById('chatMessages');
  const bookForm = document.getElementById('bookForm');
  const bookResult = document.getElementById('bookResult');

  toggle.addEventListener('click', () => {
    box.classList.toggle('hidden');
    // welcome message
    if (!body.querySelector('.msg-bot')) {
      setTimeout(()=> append('bot', "Hi! I can help you book and suggest hairstyles/products. Try: 'Book haircut on 2025-12-20 at 15:00 for Rahul 9876543210 male 28' or 'Recommend hairstyle for round face fair skin female 28'."), 200);
    }
  });

  closeBtn && closeBtn.addEventListener('click', () => box.classList.add('hidden'));

  function append(who, text) {
    const el = document.createElement('div');
    el.className = who === 'user' ? 'msg-user' : 'msg-bot';
    el.textContent = text;
    body.appendChild(el);
    body.scrollTop = body.scrollHeight;
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    append('user', text);
    input.value = '';
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: text, session_id: sessionId})
      });
      const j = await res.json();
      append('bot', j.reply || j.message || 'No reply.');
    } catch (err) {
      append('bot', 'Sorry, something went wrong. Try again.');
      console.error(err);
    }
  }

  sendBtn && sendBtn.addEventListener('click', sendMessage);
  input && input.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });

  // booking form submit - remain same but include session_id when appending
  if (bookForm) {
    bookForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(bookForm);
      const payload = Object.fromEntries(formData.entries());
      bookResult.textContent = '...booking...';
      try {
        const r = await fetch('/api/book', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
        const j = await r.json();
        if (j.ok) {
          bookResult.textContent = `Booked! ID: ${j.booking_id}`;
          append('bot', `I booked ${payload.service} for ${payload.name} on ${payload.date} at ${payload.time}`);
        } else {
          bookResult.textContent = `Error: ${j.msg || 'unknown'}`;
        }
      } catch (err) {
        bookResult.textContent = 'Network error';
      }
    });
  }
});
