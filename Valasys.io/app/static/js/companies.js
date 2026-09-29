const csvDialog = document.getElementById("csv-dialog");
const csvInput = document.getElementById("csv-file");
const csvDropzone = document.getElementById("csv-dropzone");
const csvStatus = document.getElementById("csv-upload-status");
const csvPreview = document.getElementById("csv-preview");
const csvPreviewTable = document.getElementById("csv-preview-table");
const csvRowCount = document.getElementById("csv-row-count");
const finishButton = document.getElementById("finish-csv-upload");
const maxCsvDataRows = 1000;
const profileButton = document.getElementById("profileButton");
const profileDropdown = document.getElementById("profileDropdown");
const selectionTrigger = document.getElementById("company-selection-trigger");
const selectionPopup = document.getElementById("company-selection-popup");
const selectionIcon = selectionTrigger.querySelector(".selection-state-icon");
const companyActionButton = document.getElementById("company-action-button");
const companyActionIcon = document.getElementById("company-action-icon");
const companyActionLabel = document.getElementById("company-action-label");
const exportDialog = document.getElementById("company-export-dialog");
const exportCount = document.getElementById("company-export-count");
const exportFormat = document.getElementById("company-export-format");
const exportStatus = document.getElementById("company-export-status");
const confirmExportButton = document.getElementById("confirm-company-export");
const applySelectionButton = document.getElementById("apply-company-selection");
const cancelSelectionButton = document.getElementById("cancel-company-selection");
const selectionModeInputs = Array.from(
    selectionPopup.querySelectorAll('input[name="company-selection-mode"]')
);
const companyCheckboxes = Array.from(
    document.querySelectorAll(".company-select")
);
const companySelectionStorageKey = "companies-selection";

document.querySelector(".reset-button").addEventListener("click", () => {
    sessionStorage.removeItem(companySelectionStorageKey);
});

if (profileButton && profileDropdown) {
    function setProfileDropdownOpen(isOpen) {
        profileDropdown.classList.toggle("show", isOpen);
        profileButton.setAttribute("aria-expanded", String(isOpen));
    }

    profileButton.addEventListener("click", (event) => {
        event.stopPropagation();
        setProfileDropdownOpen(!profileDropdown.classList.contains("show"));
    });

    document.addEventListener("click", (event) => {
        if (
            !profileDropdown.contains(event.target) &&
            !profileButton.contains(event.target)
        ) {
            setProfileDropdownOpen(false);
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && profileDropdown.classList.contains("show")) {
            setProfileDropdownOpen(false);
            profileButton.focus();
        }
    });
}

let companySelection = {
    all: false,
    ids: [],
    excludedIds: [],
    firstCount: 0,
    mode: "page",
};

try {
    const storedSelection = JSON.parse(
        sessionStorage.getItem(companySelectionStorageKey)
    );
    if (
        storedSelection &&
        typeof storedSelection.all === "boolean" &&
        Array.isArray(storedSelection.ids) &&
        Array.isArray(storedSelection.excludedIds)
    ) {
        companySelection = {
            ...storedSelection,
            firstCount: Number.isInteger(storedSelection.firstCount)
                ? storedSelection.firstCount
                : 0,
            mode: ["page", "all"].includes(storedSelection.mode)
                ? storedSelection.mode
                : storedSelection.all
                    ? "all"
                    : "page",
        };
    }
} catch {
    sessionStorage.removeItem(companySelectionStorageKey);
}

function isCompanySelected(companyId) {
    if (companySelection.all) {
        return !companySelection.excludedIds.includes(companyId);
    }
    if (companySelection.ids.includes(companyId)) {
        return true;
    }

    const companyCheckbox = companyCheckboxes.find(
        (checkbox) => checkbox.value === companyId
    );
    return Boolean(
        companySelection.firstCount &&
        Number(companyCheckbox?.dataset.companyNumber) <= companySelection.firstCount &&
        !companySelection.excludedIds.includes(companyId)
    );
}

function saveCompanySelection() {
    sessionStorage.setItem(
        companySelectionStorageKey,
        JSON.stringify(companySelection)
    );
}

function updateSelectionIcon() {
    const selectedCount = companyCheckboxes.filter(
        (checkbox) => checkbox.checked
    ).length;

    selectionIcon.className =
        selectedCount === 0
            ? "fa-regular fa-square selection-state-icon"
            : selectedCount === companyCheckboxes.length
                ? "fa-solid fa-square-check selection-state-icon"
                : "fa-solid fa-square-minus selection-state-icon";

    updateExportActionButton();
}

function getSelectedCompanyCount() {
    if (companySelection.all) {
        return Math.max(
            0,
            Number(selectionPopup.dataset.totalCount) - companySelection.excludedIds.length
        );
    }

    return companySelection.ids.length + Math.max(
        0,
        companySelection.firstCount - companySelection.excludedIds.length
    );
}

function updateExportActionButton() {
    const hasSelection = getSelectedCompanyCount() > 0;
    companyActionIcon.className = hasSelection
        ? "fa-solid fa-download"
        : "fa-solid fa-plus";
    companyActionLabel.textContent = hasSelection ? "Export" : "Add Company";
    exportCount.textContent = getSelectedCompanyCount().toLocaleString();
}

function positionSelectionPopup() {
    const triggerBounds = selectionTrigger.getBoundingClientRect();
    const viewportPadding = 8;
    const maxLeft = Math.max(
        viewportPadding,
        window.innerWidth - selectionPopup.offsetWidth - viewportPadding
    );
    const left = Math.min(
        Math.max(viewportPadding, triggerBounds.left),
        maxLeft
    );
    const belowTop = triggerBounds.bottom + 5;
    const top = belowTop + selectionPopup.offsetHeight <= window.innerHeight - viewportPadding
        ? belowTop
        : Math.max(viewportPadding, triggerBounds.top - selectionPopup.offsetHeight - 5);

    selectionPopup.style.left = `${left}px`;
    selectionPopup.style.top = `${top}px`;
}

function closeSelectionPopup() {
    selectionPopup.hidden = true;
    selectionTrigger.setAttribute("aria-expanded", "false");
}

function openSelectionPopup() {
    selectionModeInputs.forEach((input) => {
        input.checked = input.value === companySelection.mode;
    });
    selectionPopup.hidden = false;
    selectionTrigger.setAttribute("aria-expanded", "true");
    positionSelectionPopup();
}

companyCheckboxes.forEach((checkbox) => {
    checkbox.checked = isCompanySelected(checkbox.value);
    checkbox.addEventListener("change", () => {
        if (companySelection.all) {
            companySelection.excludedIds = checkbox.checked
                ? companySelection.excludedIds.filter((id) => id !== checkbox.value)
                : [...new Set([...companySelection.excludedIds, checkbox.value])];
        } else if (
            companySelection.firstCount &&
            Number(checkbox.dataset.companyNumber) <= companySelection.firstCount
        ) {
            companySelection.excludedIds = checkbox.checked
                ? companySelection.excludedIds.filter((id) => id !== checkbox.value)
                : [...new Set([...companySelection.excludedIds, checkbox.value])];
        } else {
            companySelection.ids = checkbox.checked
                ? [...new Set([...companySelection.ids, checkbox.value])]
                : companySelection.ids.filter((id) => id !== checkbox.value);
        }
        saveCompanySelection();
        updateSelectionIcon();
    });
});

selectionTrigger.addEventListener("click", () => {
    if (selectionPopup.hidden) {
        openSelectionPopup();
    } else {
        closeSelectionPopup();
    }
});

applySelectionButton.addEventListener("click", () => {
    const selectedMode = selectionModeInputs.find((input) => input.checked)?.value;

    if (selectedMode === "all") {
        companySelection = {
            all: true,
            ids: [],
            excludedIds: [],
            firstCount: 0,
            mode: "all",
        };
    } else {
        companySelection = {
            all: false,
            ids: companyCheckboxes.map((checkbox) => checkbox.value),
            excludedIds: [],
            firstCount: 0,
            mode: "page",
        };
    }

    companyCheckboxes.forEach((checkbox) => {
        checkbox.checked = isCompanySelected(checkbox.value);
    });
    saveCompanySelection();
    updateSelectionIcon();
    closeSelectionPopup();
});

cancelSelectionButton.addEventListener("click", closeSelectionPopup);

document.addEventListener("click", (event) => {
    if (
        !selectionPopup.hidden &&
        !selectionPopup.contains(event.target) &&
        !selectionTrigger.contains(event.target)
    ) {
        closeSelectionPopup();
    }
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !selectionPopup.hidden) {
        closeSelectionPopup();
        selectionTrigger.focus();
    }
});

window.addEventListener("resize", () => {
    if (!selectionPopup.hidden) {
        positionSelectionPopup();
    }
});

window.addEventListener("scroll", () => {
    if (!selectionPopup.hidden) {
        positionSelectionPopup();
    }
}, true);

updateSelectionIcon();

companyActionButton.addEventListener("click", () => {
    if (getSelectedCompanyCount() > 0) {
        exportStatus.textContent = "";
        exportDialog.showModal();
    }
});

document.getElementById("close-company-export").addEventListener("click", () => {
    exportDialog.close();
});

document.getElementById("cancel-company-export").addEventListener("click", () => {
    exportDialog.close();
});

confirmExportButton.addEventListener("click", async () => {
    confirmExportButton.disabled = true;
    exportStatus.textContent = "Preparing your export...";

    try {
        const response = await fetch("/companies/export", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                format: exportFormat.value,
                selection: {
                    all: companySelection.all,
                    ids: companySelection.ids,
                    excludedIds: companySelection.excludedIds,
                },
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "The export could not be created.");
        }

        const file = await response.blob();
        const downloadUrl = URL.createObjectURL(file);
        const downloadLink = document.createElement("a");
        downloadLink.href = downloadUrl;
        downloadLink.download = `companies.${exportFormat.value}`;
        document.body.append(downloadLink);
        downloadLink.click();
        downloadLink.remove();
        URL.revokeObjectURL(downloadUrl);
        exportDialog.close();
    } catch (error) {
        exportStatus.textContent = error.message;
    } finally {
        confirmExportButton.disabled = false;
    }
});

function parseCsv(text) {
    const rows = [];
    let row = [];
    let cell = "";
    let insideQuotes = false;

    for (let index = 0; index < text.length; index += 1) {
        const character = text[index];

        if (character === '"') {
            if (insideQuotes && text[index + 1] === '"') {
                cell += '"';
                index += 1;
            } else {
                insideQuotes = !insideQuotes;
            }
        } else if (character === "," && !insideQuotes) {
            row.push(cell);
            cell = "";
        } else if ((character === "\n" || character === "\r") && !insideQuotes) {
            if (character === "\r" && text[index + 1] === "\n") {
                index += 1;
            }
            row.push(cell);
            if (row.some((value) => value.trim())) {
                rows.push(row);
            }
            row = [];
            cell = "";
        } else {
            cell += character;
        }
    }

    if (insideQuotes) {
        throw new Error("The CSV contains an unclosed quoted value.");
    }

    row.push(cell);
    if (row.some((value) => value.trim())) {
        rows.push(row);
    }

    return rows;
}

function showCsvPreview(headers, dataRows) {
    csvPreviewTable.replaceChildren();

    const head = document.createElement("thead");
    const headerRow = document.createElement("tr");
    headers.forEach((header) => {
        const cell = document.createElement("th");
        cell.scope = "col";
        cell.textContent = header;
        headerRow.append(cell);
    });
    head.append(headerRow);
    csvPreviewTable.append(head);

    const body = document.createElement("tbody");
    dataRows.slice(0, 5).forEach((values) => {
        const tableRow = document.createElement("tr");
        headers.forEach((_, index) => {
            const cell = document.createElement("td");
            cell.textContent = values[index] || "";
            tableRow.append(cell);
        });
        body.append(tableRow);
    });
    csvPreviewTable.append(body);
    csvRowCount.textContent = `${dataRows.length} data rows`;
    csvPreview.hidden = false;
}

async function loadCsv(file) {
    finishButton.disabled = true;
    csvPreview.hidden = true;
    csvStatus.classList.remove("is-success");
    csvStatus.textContent = "";
    csvPreviewTable.replaceChildren();

    if (!file || !file.name.toLowerCase().endsWith(".csv")) {
        csvStatus.textContent = "Choose a .csv file.";
        return;
    }

    try {
        const rows = parseCsv(await file.text());
        if (!rows.length) {
            throw new Error("The CSV file is empty.");
        }

        const headers = rows[0].map((header) => header.trim());
        headers[0] = headers[0].replace(/^\uFEFF/, "");

        if (headers.some((header) => !header)) {
            throw new Error("Every column must have a header in the first row.");
        }

        const normalizedHeaders = headers.map((header) => header.toLowerCase());
        if (new Set(normalizedHeaders).size !== normalizedHeaders.length) {
            throw new Error("Column headers must be unique.");
        }

        const filterHeaderIndices = headers.reduce((indices, header, index) => {
            if (["companies", "website"].includes(header.toLowerCase())) {
                indices.push(index);
            }
            return indices;
        }, []);
        if (filterHeaderIndices.length !== 1) {
            throw new Error(
                "CSV must contain exactly one column named Companies or Website."
            );
        }

        const dataRows = rows.slice(1);
        if (dataRows.length > maxCsvDataRows) {
            throw new Error("The CSV file cannot contain more than 1,000 rows.");
        }

        if (!dataRows.some((row) => row[filterHeaderIndices[0]]?.trim())) {
            throw new Error("The selected column does not contain any values.");
        }

        showCsvPreview(headers, dataRows);
        csvStatus.textContent = `${headers[filterHeaderIndices[0]]} column found. ${file.name} is ready to filter.`;
        csvStatus.classList.add("is-success");
        finishButton.disabled = false;
    } catch (error) {
        csvStatus.textContent = error.message;
    }
}

document.getElementById("open-csv-dialog").addEventListener("click", () => {
    csvDialog.showModal();
});

document.getElementById("close-csv-dialog").addEventListener("click", () => {
    csvDialog.close();
});

document.getElementById("cancel-csv-upload").addEventListener("click", () => {
    csvInput.value = "";
    csvPreview.hidden = true;
    finishButton.disabled = true;
    csvStatus.textContent = "";
    csvDialog.close();
});

csvInput.addEventListener("change", () => {
    loadCsv(csvInput.files[0]);
});

csvDropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
    csvDropzone.classList.add("is-dragging");
});

csvDropzone.addEventListener("dragleave", () => {
    csvDropzone.classList.remove("is-dragging");
});

csvDropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    csvDropzone.classList.remove("is-dragging");
    const [file] = event.dataTransfer.files;
    if (file) {
        const transfer = new DataTransfer();
        transfer.items.add(file);
        csvInput.files = transfer.files;
        loadCsv(file);
    }
});

csvDialog.addEventListener("click", (event) => {
    if (event.target === csvDialog) {
        csvDialog.close();
    }
});