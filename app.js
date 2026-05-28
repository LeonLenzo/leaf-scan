let srcImg = null;
let imageFiles = [];
let currentIndex = 0;
let imageSettings = {};

const SLIDER_IDS = ['contrastFactor', 'tempFactor', 'necrosisHue', 'chlorosisHue', 'healthyHue', 'minLeafSize'];
let allResults = {};

function saveSettingsForImage(filename) {
    imageSettings[filename] = {};
    SLIDER_IDS.forEach(id => {
        imageSettings[filename][id] = document.getElementById(id).value;
    });
}

function restoreSettingsForImage(filename) {
    if (!imageSettings[filename]) return;
    SLIDER_IDS.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.value = imageSettings[filename][id];
        const spanId = labelMap[id];
        if (spanId) document.getElementById(spanId).innerText = imageSettings[filename][id];
    });
}

function loadImageFile(file) {
    const reader = new FileReader();

    if (file.name.toLowerCase().match(/\.tiff?$/)) {
        reader.onload = (event) => {
            const ifds = UTIF.decode(event.target.result);
            UTIF.decodeImage(event.target.result, ifds[0]);
            const rgba = UTIF.toRGBA8(ifds[0]);
            const { width, height } = ifds[0];
            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            const imageData = ctx.createImageData(width, height);
            imageData.data.set(rgba);
            ctx.putImageData(imageData, 0, 0);
            if (srcImg) srcImg.delete();
            srcImg = cv.imread(canvas);
            updateImageNav();
            processImage();
        };
        reader.readAsArrayBuffer(file);
    } else {
        reader.onload = (event) => {
            const img = new Image();
            img.onload = () => {
                if (srcImg) srcImg.delete();
                srcImg = cv.imread(img);
                updateImageNav();
                processImage();
            };
            img.src = event.target.result;
        };
        reader.readAsDataURL(file);
    }
}

function updateImageNav() {
    const nav = document.getElementById('imageNav');
    const info = document.getElementById('imageInfo');
    if (imageFiles.length > 0) {
        nav.style.display = 'block';
        info.textContent = `${currentIndex + 1} / ${imageFiles.length}: ${imageFiles[currentIndex].name}`;
    } else {
        nav.style.display = 'none';
    }
}

function setImageQueue(files) {
    imageFiles = Array.from(files).filter(f => f.type.startsWith('image/'));
    if (imageFiles.length === 0) return;
    currentIndex = 0;
    loadImageFile(imageFiles[0]);
}

window.prevImage = () => {
    if (currentIndex > 0) {
        saveSettingsForImage(imageFiles[currentIndex].name);
        currentIndex--;
        restoreSettingsForImage(imageFiles[currentIndex].name);
        loadImageFile(imageFiles[currentIndex]);
    }
};
window.nextImage = () => {
    if (currentIndex < imageFiles.length - 1) {
        saveSettingsForImage(imageFiles[currentIndex].name);
        currentIndex++;
        restoreSettingsForImage(imageFiles[currentIndex].name);
        loadImageFile(imageFiles[currentIndex]);
    }
};

document.getElementById('imageUpload').addEventListener('change', (e) => {
    imageSettings = {};
    allResults = {};
    renderTable();
    setImageQueue(e.target.files);
});

// Event Listeners for Live Preview
const labelMap = {
    'contrastFactor': 'contrastVal',
    'tempFactor': 'tempVal',
    'necrosisHue': 'necrosisVal',
    'chlorosisHue': 'chlorosisVal',
    'healthyHue': 'healthyVal',
    'minLeafSize': 'sizeVal'
};

Object.keys(labelMap).forEach(id => {
    const el = document.getElementById(id);
    if (el) {
        el.addEventListener('input', (e) => {
            const span = document.getElementById(labelMap[id]);
            if (span) span.innerText = e.target.value;
            if (srcImg) processImage();
        });
    }
});

function processImage() {
    const contrastFactor = parseFloat(document.getElementById('contrastFactor').value);
    const tempFactor = parseFloat(document.getElementById('tempFactor').value);
    const necrosisH = parseInt(document.getElementById('necrosisHue').value);
    const chlorosisH = parseInt(document.getElementById('chlorosisHue').value);
    const healthyH = parseInt(document.getElementById('healthyHue').value);
    const minLeafSize = parseInt(document.getElementById('minLeafSize').value);

    let mat = srcImg.clone();
    
    // 1. Preprocessing
    applyTemperature(mat, tempFactor);
    mat.convertTo(mat, -1, contrastFactor, 128 * (1 - contrastFactor));
    cv.imshow('canvasOriginal', mat);

    // 2. Color Conversion
    let hsv = new cv.Mat();
    let rgb = new cv.Mat();
    cv.cvtColor(mat, rgb, cv.COLOR_RGBA2RGB);
    cv.cvtColor(rgb, hsv, cv.COLOR_RGB2HSV);

    // 3. Leaf Segmentation Mask
    let leafMask = createLeafMask(hsv, necrosisH, healthyH);
    
    // 4. Connected Components
    let labels = new cv.Mat();
    let stats = new cv.Mat();
    let centroids = new cv.Mat();
    let nLabels = cv.connectedComponentsWithStats(leafMask, labels, stats, centroids, 8, cv.CV_32S);

    // 5. Analysis Overlay
    let output = createAnalysisOverlay(mat, hsv, leafMask, necrosisH, chlorosisH);

    // Add bottom padding so labels below leaf tips are never clipped
    let padded = new cv.Mat();
    cv.copyMakeBorder(output, padded, 0, 80, 0, 0, cv.BORDER_CONSTANT, new cv.Scalar(0, 0, 0, 0));
    output.delete();

    let leafCount = 0;
    const filename = imageFiles.length > 0 ? imageFiles[currentIndex].name : 'image';
    const leafRows = [];

    for (let i = 1; i < nLabels; i++) {
        let area = stats.intAt(i, cv.CC_STAT_AREA);
        if (area < minLeafSize) continue;
        leafCount++;

        let metrics = analyzeLeafTissue(hsv, labels, i, necrosisH, chlorosisH);
        leafRows.push({ leaf: leafCount, ...metrics });

        // Place label just below the leaf bounding box, in the padded zone
        let cx = Math.round(centroids.doubleAt(i, 0));
        let leafBottom = stats.intAt(i, cv.CC_STAT_TOP) + stats.intAt(i, cv.CC_STAT_HEIGHT);
        let labelX = Math.max(5, Math.min(cx - 85, padded.cols - 175));
        let labelY = Math.min(leafBottom + 65, padded.rows - 10);
        cv.putText(padded, `Leaf ${leafCount}`, new cv.Point(labelX, labelY),
                   cv.FONT_HERSHEY_SIMPLEX, 2.0, [0, 0, 0, 255], 3);
    }

    allResults[filename] = {
        sliders: { contrastFactor, tempFactor, necrosisH, chlorosisH, healthyH, minLeafSize },
        leaves: leafRows
    };
    renderTable();

    cv.imshow('canvasOutput', padded);

    // Cleanup
    mat.delete(); rgb.delete(); hsv.delete(); leafMask.delete();
    labels.delete(); stats.delete(); centroids.delete(); padded.delete();
}

function applyTemperature(mat, factor) {
    let channels = new cv.MatVector();
    cv.split(mat, channels);
    let red = channels.get(0);
    let blue = channels.get(2);
    red.convertTo(red, -1, factor, 0);
    blue.convertTo(blue, -1, 1/factor, 0);
    cv.merge(channels, mat);
    channels.delete(); red.delete(); blue.delete();
}

function createLeafMask(hsv, necrosisH, healthyH) {
    let mask = new cv.Mat();
    let lowMat = cv.matFromArray(1, 3, cv.CV_8U, [0, 15, 15]);
    let highMat = cv.matFromArray(1, 3, cv.CV_8U, [healthyH, 255, 255]);
    cv.inRange(hsv, lowMat, highMat, mask);
    lowMat.delete(); highMat.delete();


    return mask;
}

function createAnalysisOverlay(mat, hsv, leafMask, necrosisH, chlorosisH) {
    let output = new cv.Mat(mat.rows, mat.cols, cv.CV_8UC4, new cv.Scalar(0, 0, 0, 0));
    output.setTo(new cv.Scalar(15, 55, 15, 128), leafMask);

    let necrosisMask = new cv.Mat();
    let nLow = cv.matFromArray(1, 3, cv.CV_8U, [0, 15, 15]);
    let nHigh = cv.matFromArray(1, 3, cv.CV_8U, [necrosisH, 255, 255]);
    cv.inRange(hsv, nLow, nHigh, necrosisMask);
    cv.bitwise_and(necrosisMask, leafMask, necrosisMask);

    let chlorosisMask = new cv.Mat();
    let cLow = cv.matFromArray(1, 3, cv.CV_8U, [necrosisH + 1, 15, 15]);
    let cHigh = cv.matFromArray(1, 3, cv.CV_8U, [chlorosisH, 255, 255]);
    cv.inRange(hsv, cLow, cHigh, chlorosisMask);
    cv.bitwise_and(chlorosisMask, leafMask, chlorosisMask);

    output.setTo(new cv.Scalar(166, 56, 22, 200), necrosisMask);
    output.setTo(new cv.Scalar(255, 222, 83, 200), chlorosisMask);

    necrosisMask.delete(); nLow.delete(); nHigh.delete();
    chlorosisMask.delete(); cLow.delete(); cHigh.delete();
    return output;
}

function analyzeLeafTissue(hsv, labels, labelId, necrosisH, chlorosisH) {
    let leafPixels = 0;
    let necrosis = 0;
    let chlorosis = 0;

    for (let i = 0; i < hsv.rows; i++) {
        for (let j = 0; j < hsv.cols; j++) {
            if (labels.intAt(i, j) === labelId) {
                leafPixels++;
                let h = hsv.ucharPtr(i, j)[0];
                if (h <= necrosisH) necrosis++;
                else if (h <= chlorosisH) chlorosis++;
            }
        }
    }

    let healthy = leafPixels - necrosis - chlorosis;
    return {
        healthyPerc: ((healthy / leafPixels) * 100).toFixed(1),
        necrosisPerc: ((necrosis / leafPixels) * 100).toFixed(1),
        chlorosisPerc: ((chlorosis / leafPixels) * 100).toFixed(1)
    };
}

function renderTable() {
    const tbody = document.querySelector('#statsTable tbody');
    const rows = [];
    for (const [filename, result] of Object.entries(allResults)) {
        for (const leaf of result.leaves) {
            rows.push(`<tr>
                <td>${filename}</td>
                <td>${leaf.leaf}</td>
                <td>${leaf.healthyPerc}%</td>
                <td>${leaf.necrosisPerc}%</td>
                <td>${leaf.chlorosisPerc}%</td>
            </tr>`);
        }
    }
    tbody.innerHTML = rows.reverse().join('');
}

window.downloadCSV = () => {
    const headers = ['Image', 'Leaf', 'Healthy%', 'Necrosis%', 'Chlorosis%',
                     'Contrast', 'Temperature', 'NecrosisHue', 'ChlorosisHue', 'HealthyHue', 'MinLeafSize'];
    const rows = [headers.join(',')];

    for (const [filename, result] of Object.entries(allResults)) {
        const s = result.sliders;
        for (const leaf of result.leaves) {
            rows.push([
                `"${filename}"`, leaf.leaf,
                leaf.healthyPerc, leaf.necrosisPerc, leaf.chlorosisPerc,
                s.contrastFactor, s.tempFactor, s.necrosisH, s.chlorosisH, s.healthyH, s.minLeafSize
            ].join(','));
        }
    }

    const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'leafstate_results.csv';
    a.click();
    URL.revokeObjectURL(a.href);
};

window.stepUp = (id) => {
    const el = document.getElementById(id);
    if (el) { el.stepUp(); el.dispatchEvent(new Event('input')); }
};
window.stepDown = (id) => {
    const el = document.getElementById(id);
    if (el) { el.stepDown(); el.dispatchEvent(new Event('input')); }
};

// ── Theme toggle ──
const THEMES = ['default', 'light', 'dark'];
const THEME_LABELS = { default: '💻 Auto', light: '☀️ Light', dark: '🌙 Dark' };

(function initTheme() {
    const saved = localStorage.getItem('theme') || 'default';
    document.documentElement.dataset.theme = saved;
    document.addEventListener('DOMContentLoaded', () => {
        document.getElementById('themeToggle').textContent = THEME_LABELS[saved];
    });
})();

window.cycleTheme = () => {
    const current = document.documentElement.dataset.theme || 'default';
    const next = THEMES[(THEMES.indexOf(current) + 1) % THEMES.length];
    document.documentElement.dataset.theme = next;
    document.getElementById('themeToggle').textContent = THEME_LABELS[next];
    localStorage.setItem('theme', next);
};

// OpenCV.js ready callback
var Module = {
    onRuntimeInitialized() {
        document.getElementById('status').innerHTML = '✅ OpenCV.js Ready';
        document.getElementById('status').style.color = 'green';
    }
};