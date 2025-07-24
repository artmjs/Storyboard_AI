const raw = sessionStorage.getItem('panelsToRefine');
if(!raw) {
  document.body.innerHTML = '<p>No panels to refine. Go back and select some.</p>';
  throw 'No panels';
}
const panels = JSON.parse(raw);
const list = document.getElementById('panelList');

// 2) Render each panel top-down
panels.forEach(panel => {
  const card = document.createElement('div');
  card.style.margin = '20px 0';
  const title = document.createElement('h2');
  title.textContent = `Panel ${panel.id}`;
  const img = document.createElement('img');
  img.src = panel.beforeUrl;
  card.append(title, img);
  list.appendChild(card);
});