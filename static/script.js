const API_URL = "/api";
let currentData = [];

// Drag and Drop Logic
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        handleFile(e.dataTransfer.files[0]);
    }
});
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) handleFile(e.target.files[0]);
});

async function handleFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    // UI Loading
    const dropHTML = dropZone.innerHTML;
    dropZone.innerHTML = '<i class="fa-solid fa-spinner fa-spin upload-icon"></i><p>Traitement en cours...</p>';

    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.error) throw new Error(data.error);

        currentData = data.results;
        renderTable(currentData);

    } catch (e) {
        alert(e.message);
    } finally {
        dropZone.innerHTML = dropHTML;
    }
}

// --- Single Search ---
async function performSingleSearch() {
    const input = document.getElementById('singleInput').value.trim();
    if (!input) return;

    const btn = document.getElementById('singleSearchBtn');
    const originalIcon = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    btn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/categorize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input })
        });

        const data = await response.json();
        // Add to the table (top)
        renderTable([data], true); // true = append/prepend mode? Let's just prepend.

    } catch (e) {
        alert("Erreur de connexion : " + e.message);
    } finally {
        btn.innerHTML = originalIcon;
        btn.disabled = false;
    }
}

document.getElementById('singleInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSingleSearch();
});


async function processPaste() {
    const text = document.getElementById('pasteInput').value;
    const lines = text.split('\n').filter(l => l.trim());
    if (!lines.length) return;

    const btn = document.getElementById('proccessPasteBtn');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Traitement...';
    btn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ inputs: lines })
        });

        if (!response.ok) throw new Error(`Server Error: ${response.status}`);

        const data = await response.json();
        currentData = data.results;
        renderTable(currentData);

    } catch (e) {
        console.error(e);
        alert("Erreur: " + e.message + "\n(Vérifiez que le serveur python tourne bien)");
    } finally {
        btn.innerHTML = 'Enrichir les données';
        btn.disabled = false;
    }
}

function renderTable(data, prepend = false) {
    const tbody = document.getElementById('tableBody');
    if (!prepend) {
        tbody.innerHTML = '';
        currentData = data;
    } else {
        currentData = [...data, ...currentData];
    }

    if (currentData.length === 0) {
        document.getElementById('emptyState').style.display = 'block';
        return;
    }
    document.getElementById('emptyState').style.display = 'none';

    // Stats counters
    let found = 0, notFound = 0, error = 0;

    // Re-render all from currentData to keep order and stats correct
    // (A bit inefficient but safe)
    tbody.innerHTML = '';

    currentData.forEach(row => {
        // Stats
        if (row["Secteur"].includes("Non Trouvé") || row["Secteur"] === "Unknown") notFound++;
        else found++;

        const tr = document.createElement('tr');

        const statusIcon = (row["Secteur"].includes("Non Trouvé") || row["Secteur"] === "Unknown") ?
            '<i class="fa-solid fa-circle-exclamation status-icon warning"></i>' :
            '<i class="fa-solid fa-circle-check status-icon success"></i>';

        const sector = row["Secteur"] === "Unknown" ? "Non Trouvé" : row["Secteur"];
        const region = row["Région"] || "Non renseigné";
        const headcount = row["Effectif"] || "Non renseigné";
        const link = row["Lien"] && row["Lien"] !== "#" ? `<a href="${row["Lien"]}" target="_blank" class="link-btn">Voir <i class="fa-solid fa-arrow-up-right-from-square"></i></a>` : "-";

        tr.innerHTML = `
            <td>${statusIcon}</td>
            <td>${row["Input"]}</td>
            <td><strong>${row["Nom Officiel"]}</strong></td>
            <td><span class="industry-badge">${sector}</span></td>
            <td>${row["Adresse"]}</td>
            <td>${region}</td>
            <td>${headcount}</td>
            <td>${link}</td>
        `;
        tbody.appendChild(tr);
    });

    // Update Header and Footer Counts
    document.getElementById('countTotal').innerText = currentData.length;
    document.getElementById('pluralTotal').innerText = currentData.length > 1 ? 's' : '';

    document.getElementById('statFound').innerText = found;
    document.getElementById('statNotFound').innerText = notFound;
    document.getElementById('statError').innerText = error;
}

function downloadExcel() {
    // Reusing the CSV logic for simplicity but naming it xls for user happiness
    // or really do Excel. For now, CSV is safer client side.
    if (currentData.length === 0) return;

    const header = ["Input", "Nom Entreprise", "Industrie", "Adresse", "Région", "Effectif", "Lien", "Score", "Détails"];
    const rows = [header.join(',')];

    currentData.forEach(row => {
        const line = [
            `"${row["Input"]}"`,
            `"${row["Nom Officiel"]}"`,
            `"${row["Secteur"]}"`,
            `"${row["Adresse"]}"`,
            `"${row["Région"]}"`,
            `"${row["Effectif"]}"`,
            `"${row["Lien"]}"`,
            `"${row["Score"]}"`,
            `"${row["Détail"]}"`
        ];
        rows.push(line.join(','));
    });

    const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `export_entreprises_${Date.now()}.csv`;
    a.click();
}
