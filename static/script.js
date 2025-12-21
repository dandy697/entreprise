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
        // Add to the table (top) - PREPEND to keep history
        currentData = [data, ...currentData];
        renderTable(currentData);

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
        .filter(l => !l.toLowerCase().includes("voir fiche"))
        .filter(l => !l.toLowerCase().includes("page suivante"))
        .filter(l => !l.toLowerCase().includes("page précédente"));

    if (lines.length === 0) return;

    const btn = document.getElementById('proccessPasteBtn');
    const progressContainer = document.getElementById('progressContainer');

    // UI Reset
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Traitement...';
    btn.disabled = true;
    progressContainer.style.display = 'block';

    // Clear previous results for new search
    currentData = [];
    renderTable(currentData);

    // Init Progress
    const total = lines.length;
    let processed = 0;
    updateProgress(0, total);

    // Sequential Processing (Chunking client-side)
    try {
        for (const line of lines) {
            try {
                // Call Single Item Endpoint
                const response = await fetch(`${API_URL}/categorize`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ input: line })
                });

                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                const data = await response.json();

                // Result Logic: Match list order (Append)
                currentData = [...currentData, ...[data]];
                renderTable(currentData);

            } catch (innerError) {
                console.error(`Error processing ${line}:`, innerError);
            }

            processed++;
            updateProgress(processed, total);
        }

    } catch (e) {
        console.error(e);
        alert("Erreur globale: " + e.message);
    } finally {
        btn.innerHTML = 'Enrichir les données';
        btn.disabled = false;

        setTimeout(() => {
            // progressContainer.style.display = 'none';
        }, 3000);
    }
}

function updateProgress(current, total) {
    const percent = Math.round((current / total) * 100);
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressPercent = document.getElementById('progressPercent');

    if (progressBar) progressBar.style.width = `${percent}%`;
    if (progressText) progressText.innerText = `${current} / ${total}`;
    if (progressPercent) progressPercent.innerText = `${percent}%`;
}

function renderTable(data) {
    const tbody = document.getElementById('tableBody');
    currentData = data;

    if (currentData.length === 0) {
        document.getElementById('emptyState').style.display = 'block';
        tbody.innerHTML = '';
        document.getElementById('countTotal').innerText = 0;
        document.getElementById('statFound').innerText = 0;
        document.getElementById('statNotFound').innerText = 0;
        document.getElementById('statError').innerText = 0;
        return;
    }
    document.getElementById('emptyState').style.display = 'none';

    let found = 0, notFound = 0, error = 0;
    tbody.innerHTML = '';

    currentData.forEach(row => {
        if (row["Secteur"].includes("Erreur") || row["Secteur"] === "Error") error++;
        else if (row["Secteur"].includes("Non Trouvé") || row["Secteur"] === "Unknown") notFound++;
        else found++;

        const tr = document.createElement('tr');
        const index = currentData.indexOf(row);

        let statusIcon = '<i class="fa-solid fa-circle-check status-icon success"></i>';
        if (row["Secteur"].includes("Erreur") || row["Secteur"] === "Error") {
            statusIcon = '<i class="fa-solid fa-circle-xmark status-icon error" style="color: var(--error);"></i>';
        } else if (row["Secteur"].includes("Non Trouvé") || row["Secteur"] === "Unknown") {
            statusIcon = '<i class="fa-solid fa-circle-exclamation status-icon warning" style="color: var(--warning);"></i>';
        }

        const sector = row["Secteur"] === "Unknown" ? "Non Trouvé" : row["Secteur"];
        const region = row["Région"] || "Non renseigné";

        let link = row["Lien"] && row["Lien"] !== "#" ? `<a href="${row["Lien"]}" target="_blank" class="link-btn">Voir <i class="fa-solid fa-arrow-up-right-from-square"></i></a>` : "-";
        if (row["Adresse"] && (row["Adresse"].includes("USA") || row["Adresse"].includes("United States"))) {
            link = '<span class="text-muted" title="Lien masqué pour USA">-</span>';
        }

        let sectorDisplay;
        if (row._isEditing) {
            const isCustom = typeof CUSTOM_SECTORS !== 'undefined' && CUSTOM_SECTORS.includes(sector);
            let sectorSelect = `<div id="sector-container-${index}" class="edit-container" style="width:100%">
                <select class="sector-select" onchange="if(this.value === 'CUSTOM') { switchToInput(${index}); } else { updateSector(${index}, this.value); }">`;

            let currentInList = false;
            ALL_SECTORS.forEach(s => {
                const selected = s === row["Secteur"] ? "selected" : "";
                if (selected) currentInList = true;
                sectorSelect += `<option value="${s}" ${selected}>${s}</option>`;
            });
            if (!currentInList) sectorSelect += `<option value="${row["Secteur"]}" selected>${row["Secteur"]}</option>`;
            sectorSelect += `<option value="CUSTOM" style="font-weight:bold; color:var(--primary-color);">✍️ Autre / Saisie libre...</option></select>`;

            if (isCustom) {
                const safeSector = sector.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;');
                sectorSelect += `<button class="delete-btn" onclick="event.stopPropagation(); deleteCustomSector('${safeSector}')" title="Supprimer"><i class="fa-solid fa-trash"></i></button>`;
            }
            sectorSelect += `<button class="cancel-btn" onclick="cancelEdit(${index})" title="Annuler"><i class="fa-solid fa-xmark"></i></button></div>`;
            sectorDisplay = sectorSelect;
        } else {
            let competitorBadge = "";
            if (row["IsCompetitor"]) {
                competitorBadge = `<span class="competitor-alert" title="Concurrent Identifié">⚠️ Concurrent</span> `;
            }
            // PILL STYLE HERE
            sectorDisplay = `
                <div class="row-display" onclick="enableEdit(${index})">
                    ${competitorBadge}
                    <span class="sector-pill">${sector}</span>
                    <i class="fa-solid fa-pen-to-square edit-icon"></i>
                </div>
            `;
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

    document.getElementById('countTotal').innerText = currentData.length;
    document.getElementById('statFound').innerText = found;
    document.getElementById('statNotFound').innerText = notFound;
    document.getElementById('statError').innerText = error;
}

async function downloadExcel() {
    if (currentData.length === 0) return;

    const btn = document.querySelector('button[onclick="downloadExcel()"]');
    const originalContent = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Export...';
    btn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/export_excel`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ results: currentData })
        });

        if (!response.ok) throw new Error("Erreur export");

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `enrichissement_export_${Date.now()}.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

    } catch (e) {
        alert("Erreur lors de l'export Excel: " + e.message);
    } finally {
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}

async function updateSector(index, newSector) {
    if (!newSector) return;

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

        if (res.is_new) {
            if (!ALL_SECTORS.includes(newSector)) ALL_SECTORS.push(newSector);
            if (typeof CUSTOM_SECTORS !== 'undefined' && !CUSTOM_SECTORS.includes(newSector)) CUSTOM_SECTORS.push(newSector);
            ALL_SECTORS.sort();
        }

    } catch (e) {
        console.error("Save failed", e);
    }
}

async function deleteCustomSector(sectorName) {
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

function showConfirm(title, message, onConfirm) {
    const modal = document.getElementById('confirmModal');
    document.getElementById('confirmTitle').innerText = title;
    document.getElementById('confirmMessage').innerText = message;

    const oldConfirm = document.getElementById('btnConfirm');
    const newConfirm = oldConfirm.cloneNode(true);
    oldConfirm.parentNode.replaceChild(newConfirm, oldConfirm);

    const oldCancel = document.getElementById('btnCancel');
    const newCancel = oldCancel.cloneNode(true);
    oldCancel.parentNode.replaceChild(newCancel, oldCancel);

    newConfirm.onclick = () => {
        onConfirm();
        modal.style.display = 'none';
    };
    newCancel.onclick = () => {
        modal.style.display = 'none';
    };

    modal.style.display = 'flex';
}

window.deleteCustomSector = deleteCustomSector;

function enableEdit(index) {
    currentData[index]._isEditing = true;
    renderTable(currentData);
}

function cancelEdit(index) {
    currentData[index]._isEditing = false;
    renderTable(currentData);
}
