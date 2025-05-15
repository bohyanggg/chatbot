function showSuggestions(questions) {
  const container = document.getElementById('suggestions');
  container.innerHTML = '<b>Suggested Questions:</b><br>';
  questions.forEach(q => {
    const btn = document.createElement('button');
    btn.innerText = q;
    btn.style.margin = '0.3rem';
    btn.onclick = () => {
      msgInput.value = q;
      send();
      container.innerHTML = '';
    };
    container.appendChild(btn);
  });
}
const chatDiv = document.getElementById('chat');
const msgInput = document.getElementById('msg');
const sessionId = localStorage.sessionId || crypto.randomUUID();

if (!localStorage.sessionId) localStorage.sessionId = sessionId;

function append(who, text) {
  const el = document.createElement('div');
  el.className = who;
  el.innerText = text;
  chatDiv.appendChild(el);
  chatDiv.scrollTop = chatDiv.scrollHeight;
}

async function send() {
  const text = msgInput.value.trim();
  if (!text) return;
  append('user', text);
  msgInput.value = '';
  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type':'application/json' },
      body: JSON.stringify({ session_id: sessionId, message: text })
    });
    const data = await res.json();
    console.log('API response:', data); 
    append('bot', data.response);
  } catch(err) {
    console.error(err);
    append('bot', 'Error contacting server.');
  }
}

window.onload = () => {
  // Trigger initial greeting
  fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message: '' })
  })
  .then(res => res.json())
  .then(data => {
    append('bot', data.response);
    showSuggestions([
      "How do I choose between daily and monthly lenses?",
      "Can I sleep with my lenses on?",
      "Are there lenses for dry eyes?"
    ]);
  })
  .catch(err => {
    console.error(err);
    append('bot', 'Error loading welcome message.');
  });
};