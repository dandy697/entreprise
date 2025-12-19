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
    }
});

// Helper for switching to custom input
window.switchToInput = function (index) {
    const container = document.getElementById(`sector-container-${index}`);
    // Replace with input
    // Replace with input
    container.innerHTML = `
        <input type="text" class="sector-input" 
        value="" placeholder="Saisissez le secteur..." 
        onchange="updateSector(${index}, this.value)" 
        onkeydown="if(event.key === 'Enter') this.blur()" autofocus>
        <button class="cancel-btn" onclick="cancelEdit(${index})" title="Annuler"><i class="fa-solid fa-xmark"></i></button>
    `;
    container.querySelector('input').focus();
};

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
    const lines = text.split('\n')
        .map(l => l.trim())
        .filter(l => l.length > 0)
        // Filter out navigation artifacts (common copy-paste junk)
        .filter(l => !l.toLowerCase().includes("voir fiche"))
        .filter(l => !l.toLowerCase().includes("page suivante"))
        .filter(l => !l.toLowerCase().includes("page précédente"));

    if (lines.length === 0) return;

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
        if (row["Secteur"].includes("Erreur") || row["Secteur"] === "Error") error++;
        else if (row["Secteur"].includes("Non Trouvé") || row["Secteur"] === "Unknown") notFound++;
        else found++;

        const tr = document.createElement('tr');
        const index = currentData.indexOf(row); // Get index for update

        let statusIcon = '<i class="fa-solid fa-circle-check status-icon success"></i>';

        if (row["Secteur"].includes("Erreur") || row["Secteur"] === "Error") {
            statusIcon = '<i class="fa-solid fa-circle-xmark status-icon error" style="color: var(--error);"></i>';
        } else if (row["Secteur"].includes("Non Trouvé") || row["Secteur"] === "Unknown") {
            statusIcon = '<i class="fa-solid fa-circle-exclamation status-icon warning" style="color: var(--warning);"></i>';
        } else {
            statusIcon = '<i class="fa-solid fa-circle-check status-icon success" style="color: var(--success);"></i>';
        }

        const sector = row["Secteur"] === "Unknown" ? "Non Trouvé" : row["Secteur"];
        const region = row["Région"] || "Non renseigné";

        // Logic: Hide link for US companies
        let link = row["Lien"] && row["Lien"] !== "#" ? `<a href="${row["Lien"]}" target="_blank" class="link-btn">Voir <i class="fa-solid fa-arrow-up-right-from-square"></i></a>` : "-";
        if (row["Adresse"] && (row["Adresse"].includes("USA") || row["Adresse"].includes("United States"))) {
            link = '<span class="text-muted" title="Lien masqué pour USA">-</span>';
        }

        // Edit Mode Logic
        let sectorDisplay;
        if (row._isEditing) {
            // Dropdown logic
            const isCustom = typeof CUSTOM_SECTORS !== 'undefined' && CUSTOM_SECTORS.includes(sector);

            let sectorSelect = `<div id="sector-container-${index}" class="edit-container" style="width:100%">
                <select class="sector-select" onchange="if(this.value === 'CUSTOM') { switchToInput(${index}); } else { updateSector(${index}, this.value); }">`;

            let currentInList = false;
            ALL_SECTORS.forEach(s => {
                const selected = s === row["Secteur"] ? "selected" : "";
                if (selected) currentInList = true;
                sectorSelect += `<option value="${s}" ${selected}>${s}</option>`;
            });

            // If currently showing a custom value NOT in list (shouldn't happen if persisted, but safety)
            if (!currentInList) {
                sectorSelect += `<option value="${row["Secteur"]}" selected>${row["Secteur"]}</option>`;
            }

            sectorSelect += `<option value="CUSTOM" style="font-weight:bold; color:var(--primary-color);">✍️ Autre / Saisie libre...</option>`;
            sectorSelect += `</select>`;

            // Buttons: Delete (if custom) OR Cancel
            if (isCustom) {
                const safeSector = sector.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;');
                sectorSelect += `<button class="delete-btn" onclick="event.stopPropagation(); deleteCustomSector('${safeSector}')" title="Supprimer ce secteur"><i class="fa-solid fa-trash"></i></button>`;
            }
            sectorSelect += `<button class="cancel-btn" onclick="cancelEdit(${index})" title="Annuler"><i class="fa-solid fa-xmark"></i></button>`;
            sectorSelect += `</div>`;

            sectorDisplay = sectorSelect;

        } else {
            // Text + Pencil
            sectorDisplay = `<div class="industry-wrapper"><span class="industry-badge">${sector}</span> <i class="fa-solid fa-pen edit-icon" onclick="enableEdit(${index})"></i></div>`;
        }

        tr.innerHTML = `
            <td>${statusIcon}</td>
            <td>${row["Input"]}</td>
            <td><strong>${row["Nom Officiel"]}</strong></td>
            <td>${sectorDisplay}</td>
            <td>${row["Adresse"]}</td>
            <td>${region}</td>
            <td>${link}</td>
        `;
        tbody.appendChild(tr);
    });

    // Update Header and Footer Counts
    document.getElementById('countTotal').innerText = currentData.length;
    // document.getElementById('pluralTotal').innerText = currentData.length > 1 ? 's' : '';

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

async function updateSector(index, newSector) {
    if (!newSector) return;

    // Optimistic Update
    const companyName = currentData[index]["Input"];
    currentData[index]["Secteur"] = newSector;
    currentData[index]._isEditing = false;
    renderTable(currentData);

    try {
        const response = await fetch(`${API_URL}/override`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: companyName, sector: newSector })
        });
        const res = await response.json();

        // Update Local Lists if New
        if (res.is_new) {
            if (!ALL_SECTORS.includes(newSector)) ALL_SECTORS.push(newSector);
            if (typeof CUSTOM_SECTORS !== 'undefined' && !CUSTOM_SECTORS.includes(newSector)) CUSTOM_SECTORS.push(newSector);
            ALL_SECTORS.sort();
        }

    } catch (e) {
        console.error("Save failed", e);
        // Ideally revert UI here
    }
}

async function deleteCustomSector(sectorName) {
    // Custom Modal Confirmation
    showConfirm(
        "Suppression",
        `Voulez-vous vraiment supprimer le secteur "${sectorName}" de la liste ?`,
        async () => {
            try {
                const response = await fetch(`${API_URL}/delete_sector`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sector: sectorName })
                });

                if (response.ok) {
                    const aidx = ALL_SECTORS.indexOf(sectorName);
                    if (aidx > -1) ALL_SECTORS.splice(aidx, 1);

                    const cidx = CUSTOM_SECTORS.indexOf(sectorName);
                    if (cidx > -1) CUSTOM_SECTORS.splice(cidx, 1);

                    renderTable(currentData);
                } else {
                    alert("Erreur serveur lors de la suppression");
                }
            } catch (e) {
                console.error(e);
                alert("Erreur suppression");
            }
        }
    );
}

// --- Custom Modal Logic ---
function showConfirm(title, message, onConfirm) {
    const modal = document.getElementById('confirmModal');
    document.getElementById('confirmTitle').innerText = title;
    document.getElementById('confirmMessage').innerText = message;

    // Reset Buttons (Clone to remove listeners)
    const oldConfirm = document.getElementById('btnConfirm');
    const newConfirm = oldConfirm.cloneNode(true);
    oldConfirm.parentNode.replaceChild(newConfirm, oldConfirm);

    const oldCancel = document.getElementById('btnCancel');
    const newCancel = oldCancel.cloneNode(true);
    oldCancel.parentNode.replaceChild(newCancel, oldCancel);

    // Bind
    newConfirm.onclick = () => {
        onConfirm();
        modal.style.display = 'none';
    };
    newCancel.onclick = () => {
        modal.style.display = 'none';
    };

    modal.style.display = 'flex';
}

// Expose to window for inline onclick
window.deleteCustomSector = deleteCustomSector;

function enableEdit(index) {
    currentData[index]._isEditing = true;
    renderTable(currentData);
}

function cancelEdit(index) {
    currentData[index]._isEditing = false;
    renderTable(currentData);
}
