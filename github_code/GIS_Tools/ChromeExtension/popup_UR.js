document.addEventListener('DOMContentLoaded', () => {
  const htmlBtn     = document.getElementById('extract-html');
  const textBtn     = document.getElementById('extract-text');
  const filesBtn    = document.getElementById('extract-files');
  const downloadBtn = document.getElementById('download');
  const outputEl    = document.getElementById('output');

  // ─── Diggers extraction ───────────────────────────────────────────────────
  htmlBtn.addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.url.includes('lightning.force.com')) {
      return alert('Navigate to a Salesforce record page first.');
    }
    chrome.scripting.executeScript({
      target: { tabId: tab.id, allFrames: false },
      func: extractDiggers
    }, (res) => {
      const r = res?.[0]?.result;
      if (!r) return alert('❗️Could not extract from Diggers iframe.');

      const filename = `Diggers_Hotline_Ticket_${r.ticket}.txt`;
      downloadBtn.dataset.type     = 'text';
      downloadBtn.dataset.filename = filename;
      downloadBtn.disabled         = false;

      outputEl.value = [
        filename,
        `Name:        ${r.caller}`,
        `Company:     ${r.company}`,
        `Working For: ${r.workFor}`,

        `Number:      ${r.cell}`,
        `Email:       ${r.email}`,
        `Coordinate1: ${r.lon}, ${r.lat}`,
        `Coordinate2: ${r.lon2}, ${r.lat2}`
      ].join('\n');
    });
  });

  // ─── IUPPS extraction ─────────────────────────────────────────────────────
  textBtn.addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    chrome.scripting.executeScript({
      target: { tabId: tab.id, allFrames: false },
      func: extractIupps
    }, (res) => {
      const r = res?.[0]?.result;
      if (!r) return alert('❗️No IUPPS data found.');

      const filename = sanitizeFilename(r.nameText) + '.txt';
      downloadBtn.dataset.type     = 'text';
      downloadBtn.dataset.filename = filename;
      downloadBtn.disabled         = false;

      outputEl.value = [
        filename,
        `Company:     ${r.company}`,
        `Type:        ${r.type}`,
        `Caller:      ${r.caller}`,
        `Phone:       ${r.phone}`,
        `Email:       ${r.email}`,
        `Coordinate1: ${r.lonW}, ${r.latN}`,
        `Coordinate2: ${r.lonE}, ${r.latS}`
      ].join('\n');
    });
  });

  // ─── GML / XML attachments extraction ────────────────────────────────────
  filesBtn.addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    chrome.scripting.executeScript({
      target: { tabId: tab.id, allFrames: false },
      func: extractMissdig
    }, (res) => {
      const list = res?.[0]?.result || [];
      if (!list.length) return alert('⚠️ No .gml or .xml attachments found.');

      downloadBtn.dataset.type = 'attachments';
      downloadBtn.dataset.list = JSON.stringify(list);
      downloadBtn.disabled = false;
      outputEl.value = list.map(item => item.filename).join('\n');
    });
  });

  // ─── Shared download handler ─────────────────────────────
  downloadBtn.addEventListener('click', async () => {
    const type = downloadBtn.dataset.type;
    if (type === 'attachments') {
      const list = JSON.parse(downloadBtn.dataset.list);
      for (const { url, filename } of list) {
        try {
          const resp = await fetch(url, { credentials: 'include' });
          const blob = await resp.blob();
          const objUrl = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = objUrl;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(objUrl);
        } catch (err) {
          console.error('Download failed for', filename, err);
          alert(`Failed to download ${filename}: ${err.message}`);
        }
      }
      return;
    }

    const data = outputEl.value;
    if (!data) return alert('Nothing to download.');
    const mime = type === 'html' ? 'text/html' : 'text/plain';
    const blob = new Blob([data], { type: mime });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = downloadBtn.dataset.filename;
    a.click();
    URL.revokeObjectURL(url);
  });
});

// ─── Content script: extract Diggers Hotline iframe ─────────────────────────
function extractDiggers() {
  const iframes = Array.from(document.querySelectorAll('#emailuiFrame'));
  // …then only keep the one that’s actually visible on screen
  const iframeEl = iframes.find(el => el.offsetParent !== null);
  if (!iframeEl) return null;
  const doc = iframeEl.contentDocument || iframeEl.contentWindow.document;
  if (!doc) return null;

  // Ticket #
  const bodyText = doc.body.innerText || '';
  const m = bodyText.match(/Ticket #:\s*(\d+)/);
  const ticket = m ? m[1] : 'unknown';

  // All tables
  const tables = Array.from(doc.querySelectorAll('table'));

  // Contact info
  const contactTable = tables.find(tbl =>
    Array.from(tbl.querySelectorAll('td'))
         .some(td => td.textContent.trim().startsWith('Caller:'))
  );
  let caller = '', company = '', workFor = '', email = '', cell = '';
  if (contactTable) {
    contactTable.querySelectorAll('tr').forEach(row => {
      const tds = Array.from(row.querySelectorAll('td'));
      for (let i = 0; i + 1 < tds.length; i += 2) {
        const label = tds[i].textContent.trim().replace(/:$/, '');
        const val   = tds[i+1].textContent.trim();
        if (label === 'Caller')      caller  = val;
        if (label === 'Company')     company = val;
        if (label === 'Working For') workFor = val;
        if (label === 'Email')       email   = val;
        if (label === 'Cell')        cell    = val;
      }
    });
  }

  // Coordinates
  const coordTable = tables.find(tbl =>
    Array.from(tbl.querySelectorAll('td'))
         .some(td => td.textContent.trim().startsWith('Latitude:'))
  );
  let lat='', lon='', lat2='', lon2='';
  if (coordTable) {
    coordTable.querySelectorAll('tr').forEach(row => {
      const tds = Array.from(row.querySelectorAll('td'));
      for (let i = 0; i + 1 < tds.length; i += 2) {
        const label = tds[i].textContent.trim().replace(/:$/, '');
        const val   = tds[i+1].textContent.trim();
        if (label === 'Latitude')            lat  = val;
        if (label === 'Longitude')           lon  = val;
        if (label === 'Secondary Latitude')  lat2 = val;
        if (label === 'Secondary Longitude') lon2 = val;
      }
    });
  }

  return { ticket, caller, company, workFor, email, cell, lat, lon, lat2, lon2 };
}

function extractIupps() {
  const txt = document.body.innerText || '';

  // ——— 1) Dynamic “nameText” exactly like extractDynamicByDate did ———
  const visible = sel =>
    Array.from(document.querySelectorAll(sel))
         .filter(el => el.offsetWidth > 0 && el.offsetHeight > 0);

  // a) Try the lightning record field with a YYYY/MM/DD in it
  const nameEls   = visible('lightning-formatted-text[data-output-element-id="output-field"]');
  const dateRegex = /\d{4}\/\d{2}\/\d{2}/;
  const nameEl    = nameEls.find(el => dateRegex.test(el.innerText)) || nameEls[0];
  let nameText    = nameEl?.innerText.trim() || '';

  // b) Fallback: first line beginning “IUPPS…”
  if (!nameText) {
    const m = txt.match(/^IUPPS[^\r\n]*/m);
    nameText = m ? m[0].trim() : 'IUPPS_Ticket';
  }

  // strip any trailing “Edit Subject”
  nameText = nameText.replace(/\s*Edit\s*Subject$/i, '').trim();

  // ——— 2) All your other fields from the plain text ———
  const company = (txt.match(/Company\s*:\s*([^\r\n]+)/i) || [])[1]?.trim() || '';
  const type    = (txt.match(/Type\s*:\s*([^\r\n]+)/i)    || [])[1]?.trim() || '';
  const caller  = (txt.match(/Caller\s*:\s*([^\r\n]+?)(?=\s*(Phone|Mobile):|$)/i) || [])[1]?.trim() || '';

  // Phone / Mobile fallback
  let phone = '';
  let m = txt.match(/Phone\s*:\s*([^\r\n]+)/i);
  if (m && m[1].trim()) {
    phone = m[1].trim();
  } else {
    m = txt.match(/Mobile\s*:\s*([^\r\n]+)/i);
    phone = m ? m[1].trim() : '';
  }

  const email = (txt.match(/Email\s*:\s*([^\r\n]+)/i) || [])[1]?.trim() || '';

  // Boundary → latN, latS, lonW, lonE
  const b = txt.match(/Boundary\s*:\s*n\s*([\d.]+)\s*s\s*([\d.]+)\s*w\s*([-\d.]+)\s*e\s*([-\d.]+)/i) || [];
  const latN = b[1] || '';
  const latS = b[2] || '';
  const lonW = b[3] || '';
  const lonE = b[4] || '';

  return { nameText, company, type, caller, phone, email, lonW, latN, lonE, latS };
}


function extractMissdig() {
  // 1) grab all attachment lists
  const lists = Array.from(document.querySelectorAll('ul.uiAbstractList'));

  // 2) pick only the one in view
  const visibleList = lists.find(ul => ul.offsetParent !== null);
  if (!visibleList) return [];

  // 3) filter its items for GML/XML
  return Array.from(visibleList.querySelectorAll('li a'))
    .map(a => {
      const span = a.querySelector('.itemTitle');
      if (!span) return null;
      const filename = span.innerText.trim();
      const ext = filename.split('.').pop().toLowerCase();
      if (ext !== 'gml' && ext !== 'xml') return null;

      let url;
      const href = a.href;
      if (/\.(gml|xml)(\?.*)?$/.test(href)) {
        url = href;
      } else if (/\/lightning\/r\/ContentDocument\/([^\/]+)/.test(href)) {
        const docId = href.match(/\/lightning\/r\/ContentDocument\/([^\/]+)/)[1];
        url = `${location.origin}/sfc/servlet.shepherd/document/download/${docId}`;
      } else {
        url = href.replace(/\/view(\?.*)?$/, '/download$1');
      }

      return { filename, url };
    })
    .filter(Boolean);
}


// ─── Helper: sanitize filenames ────────────────────────────────────────────
function sanitizeFilename(name) {
  return name.replace(/[\\/:"*?<>|]+/g, '-')
             .replace(/\s+/g, ' ')
             .trim()
             .slice(0, 100);
}
