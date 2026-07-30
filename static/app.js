/**
 * Glossalations - Frontend Application
 * Handles tabs, text/PDF/clip/OCR translation via REST, live transcription via WebSocket.
 * Features: toast notifications, loading skeletons, char count, copy/download,
 *           theme toggle, language badges, translation history, romanization.
 */

// === LANGUAGE CODE → NAME MAP ===
const LANG_NAMES = {
    af:'Afrikaans',ar:'Arabic',bn:'Bengali',bs:'Bosnian',ca:'Catalan',cs:'Czech',
    cy:'Welsh',da:'Danish',de:'German',el:'Greek',en:'English',eo:'Esperanto',
    es:'Spanish',et:'Estonian',fi:'Finnish',fr:'French',gu:'Gujarati',hi:'Hindi',
    hr:'Croatian',hu:'Hungarian',id:'Indonesian',is:'Icelandic',it:'Italian',
    ja:'Japanese',jw:'Javanese',kn:'Kannada',ko:'Korean',la:'Latin',lv:'Latvian',
    mk:'Macedonian',ml:'Malayalam',mr:'Marathi',ms:'Malay',my:'Myanmar',ne:'Nepali',
    nl:'Dutch',no:'Norwegian',pa:'Punjabi',pl:'Polish',pt:'Portuguese',ro:'Romanian',
    ru:'Russian',si:'Sinhala',sk:'Slovak',sq:'Albanian',sr:'Serbian',su:'Sundanese',
    sv:'Swedish',sw:'Swahili',ta:'Tamil',te:'Telugu',th:'Thai',tl:'Filipino',
    tr:'Turkish',uk:'Ukrainian',ur:'Urdu',vi:'Vietnamese','zh-CN':'Chinese',
    'zh-TW':'Chinese (Traditional)'
};

const LANG_FLAGS = {};

// === TOAST SYSTEM ===
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 200);
    }, 3000);
}

// === THEME TOGGLE ===
function initTheme() {
    const saved = localStorage.getItem('glossalations-theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);

    document.getElementById('themeToggle').addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('glossalations-theme', next);
    });
}

function updateThemeLabel(theme) {
    // no-op, icons handle it via CSS
}

// === HISTORY ===
function getHistory() {
    try {
        return JSON.parse(localStorage.getItem('glossalations-history') || '[]');
    } catch { return []; }
}

function saveToHistory(source, translation, romanized, targetLang, detectedLang) {
    const history = getHistory();
    history.unshift({
        source: source.substring(0, 200),
        translation: translation.substring(0, 200),
        romanized: romanized || '',
        targetLang,
        detectedLang,
        timestamp: Date.now()
    });
    // Keep last 50
    if (history.length > 50) history.length = 50;
    localStorage.setItem('glossalations-history', JSON.stringify(history));
    renderHistory();
}

function renderHistory() {
    const container = document.getElementById('textHistory');
    if (!container) return;
    const history = getHistory();
    if (history.length === 0) {
        container.innerHTML = '';
        return;
    }
    let html = '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px"><p class="label" style="margin:0">Recent translations</p><button class="btn-icon" id="clearHistoryBtn" style="font-size:11px">Clear all</button></div>';
    history.slice(0, 5).forEach((item, i) => {
        const langName = LANG_NAMES[item.targetLang] || item.targetLang;
        const time = new Date(item.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
        html += `<div class="history-item" data-index="${i}">
            <div style="display:flex; justify-content:space-between; align-items:start">
                <div style="flex:1">
                    <div class="history-source">${escapeHtml(item.source)}</div>
                    <div class="history-result">${escapeHtml(item.translation)}</div>
                    <div class="history-meta">to ${langName} - ${time}</div>
                </div>
                <button class="btn-icon history-delete" data-index="${i}" style="font-size:10px; padding:4px 8px; margin-left:8px">x</button>
            </div>
        </div>`;
    });
    container.innerHTML = html;

    // Click to restore
    container.querySelectorAll('.history-item').forEach(el => {
        el.addEventListener('click', (e) => {
            if (e.target.classList.contains('history-delete')) return;
            const idx = parseInt(el.dataset.index);
            const item = history[idx];
            if (item) {
                document.getElementById('textInput').value = item.source;
                updateCharCount('textInput', 'textCharCount');
            }
        });
    });

    // Delete individual items
    container.querySelectorAll('.history-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const idx = parseInt(btn.dataset.index);
            const h = getHistory();
            h.splice(idx, 1);
            localStorage.setItem('glossalations-history', JSON.stringify(h));
            renderHistory();
            showToast('Removed', 'info');
        });
    });

    document.getElementById('clearHistoryBtn').addEventListener('click', () => {
        localStorage.removeItem('glossalations-history');
        renderHistory();
        showToast('History cleared', 'info');
    });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// === LANGUAGE BADGE ===
function createLangBadge(langCode) {
    const name = LANG_NAMES[langCode] || langCode;
    return `<span class="lang-badge">${name}</span>`;
}

// === CHAR/WORD COUNT ===
function updateCharCount(inputId, countId) {
    const input = document.getElementById(inputId);
    const count = document.getElementById(countId);
    if (!input || !count) return;
    const text = input.value;
    const chars = text.length;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    count.textContent = `${chars} chars · ${words} words`;
}

// === COPY TO CLIPBOARD ===
function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

// === DOWNLOAD AS TXT ===
function downloadText(text, filename = 'translation.txt') {
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Downloaded!', 'success');
}

// === SKELETON HELPERS ===
function showSkeleton(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('hidden');
}
function hideSkeleton(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
}

// === INIT ===
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initTabs();
    loadLanguages();
    initTextTab();
    initPdfTab();
    initClipTab();
    initOcrTab();
    initLiveTab();
    renderHistory();
});

// === TABS ===
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
        });
    });
}

// === LANGUAGES ===
async function loadLanguages() {
    try {
        const res = await fetch('/api/languages');
        const langs = await res.json();
        const selects = ['textLang', 'pdfLang', 'clipLang', 'ocrLang', 'liveLang'];
        selects.forEach(id => {
            const select = document.getElementById(id);
            if (!select) return;
            select.innerHTML = '';
            Object.entries(langs).sort((a, b) => a[1].localeCompare(b[1])).forEach(([code, name]) => {
                const option = document.createElement('option');
                option.value = code;
                option.textContent = name;
                select.appendChild(option);
            });
            select.value = 'hi';
        });
    } catch (e) {
        showToast('Failed to load languages', 'error');
    }
}

// === TEXT TAB ===
function initTextTab() {
    const input = document.getElementById('textInput');
    input.addEventListener('input', () => updateCharCount('textInput', 'textCharCount'));

    const btn = document.getElementById('textTranslateBtn');
    btn.addEventListener('click', async () => {
        const text = input.value.trim();
        const target = document.getElementById('textLang').value;
        if (!text) { showToast('Enter some text first', 'info'); return; }

        btn.classList.add('loading');
        btn.textContent = 'Translating...';
        document.getElementById('textResult').classList.add('hidden');
        showSkeleton('textSkeleton');

        try {
            const form = new FormData();
            form.append('text', text);
            form.append('target', target);

            const res = await fetch('/api/translate-text', { method: 'POST', body: form });
            const data = await res.json();

            document.getElementById('textDetected').innerHTML = createLangBadge(data.detected_language);
            document.getElementById('textTranslation').textContent = data.translation;

            const romanizedEl = document.getElementById('textRomanized');
            if (data.romanized) {
                romanizedEl.textContent = data.romanized;
                romanizedEl.classList.remove('hidden');
            } else {
                romanizedEl.textContent = '';
                romanizedEl.classList.add('hidden');
            }

            document.getElementById('textAudio').src = data.audio_url;
            document.getElementById('textResult').classList.remove('hidden');

            // Save to history
            saveToHistory(text, data.translation, data.romanized, target, data.detected_language);
        } catch (e) {
            showToast('Translation failed: ' + e.message, 'error');
        }

        hideSkeleton('textSkeleton');
        btn.classList.remove('loading');
        btn.textContent = 'Translate';
    });

    // Copy & Download
    document.getElementById('textCopyBtn').addEventListener('click', () => {
        const translation = document.getElementById('textTranslation').textContent;
        const romanized = document.getElementById('textRomanized').textContent;
        copyText(translation + (romanized ? '\n' + romanized : ''));
    });
    document.getElementById('textDownloadBtn').addEventListener('click', () => {
        const translation = document.getElementById('textTranslation').textContent;
        const romanized = document.getElementById('textRomanized').textContent;
        downloadText(translation + (romanized ? '\n\nRomanized:\n' + romanized : ''));
    });

    document.getElementById('textSummarizeBtn').addEventListener('click', async () => {
        const text = document.getElementById('textInput').value.trim();
        if (!text) { showToast('No text to summarize', 'info'); return; }

        const summaryEl = document.getElementById('textSummary');
        summaryEl.textContent = 'Summarizing...';
        summaryEl.classList.remove('hidden');

        try {
            const form = new FormData();
            form.append('text', text);
            const res = await fetch('/api/summarize', { method: 'POST', body: form });
            const data = await res.json();
            if (data.error) {
                showToast(data.error, 'error');
                summaryEl.classList.add('hidden');
            } else {
                summaryEl.textContent = 'Summary: ' + data.summary;
            }
        } catch (e) {
            showToast('Summarization failed', 'error');
            summaryEl.classList.add('hidden');
        }
    });
}

// === PDF TAB ===
function initPdfTab() {
    const btn = document.getElementById('pdfTranslateBtn');
    btn.addEventListener('click', async () => {
        const fileInput = document.getElementById('pdfFile');
        const target = document.getElementById('pdfLang').value;
        if (!fileInput.files[0]) { showToast('Select a PDF file first', 'info'); return; }

        btn.classList.add('loading');
        btn.textContent = 'Translating...';
        document.getElementById('pdfResult').classList.add('hidden');
        showSkeleton('pdfSkeleton');

        try {
            const form = new FormData();
            form.append('file', fileInput.files[0]);
            form.append('target', target);

            const res = await fetch('/api/translate-pdf', { method: 'POST', body: form });
            const data = await res.json();

            if (data.error) {
                showToast(data.error, 'error');
            } else {
                document.getElementById('pdfOriginal').textContent = data.original_text;
                document.getElementById('pdfTranslation').textContent = data.translation;
                const pdfRomanizedEl = document.getElementById('pdfRomanized');
                if (data.romanized) {
                    pdfRomanizedEl.textContent = data.romanized;
                    pdfRomanizedEl.classList.remove('hidden');
                } else {
                    pdfRomanizedEl.textContent = '';
                    pdfRomanizedEl.classList.add('hidden');
                }
                document.getElementById('pdfAudio').src = data.audio_url;
                document.getElementById('pdfResult').classList.remove('hidden');
            }
        } catch (e) {
            showToast('PDF translation failed: ' + e.message, 'error');
        }

        hideSkeleton('pdfSkeleton');
        btn.classList.remove('loading');
        btn.textContent = 'Translate Document';
    });

    document.getElementById('pdfCopyBtn').addEventListener('click', () => {
        const translation = document.getElementById('pdfTranslation').textContent;
        const romanized = document.getElementById('pdfRomanized').textContent;
        copyText(translation + (romanized ? '\n' + romanized : ''));
    });
    document.getElementById('pdfDownloadBtn').addEventListener('click', () => {
        const translation = document.getElementById('pdfTranslation').textContent;
        const romanized = document.getElementById('pdfRomanized').textContent;
        downloadText(translation + (romanized ? '\n\nRomanized:\n' + romanized : ''), 'pdf-translation.txt');
    });
}

// === VOICE CLIP TAB ===
let clipMediaRecorder = null;
let clipChunks = [];
let clipBlob = null;

function initClipTab() {
    const recordBtn = document.getElementById('clipRecordBtn');
    const statusEl = document.getElementById('clipStatus');
    const playback = document.getElementById('clipPlayback');
    const translateBtn = document.getElementById('clipTranslateBtn');
    let isRecording = false;

    recordBtn.addEventListener('click', async () => {
        if (isRecording) {
            clipMediaRecorder.stop();
            isRecording = false;
            recordBtn.textContent = 'Record';
            recordBtn.classList.remove('recording');
            statusEl.textContent = 'Processing...';
        } else {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                clipChunks = [];
                clipMediaRecorder = new MediaRecorder(stream);
                clipMediaRecorder.ondataavailable = (e) => {
                    if (e.data.size > 0) clipChunks.push(e.data);
                };
                clipMediaRecorder.onstop = () => {
                    stream.getTracks().forEach(t => t.stop());
                    clipBlob = new Blob(clipChunks, { type: 'audio/webm' });
                    playback.src = URL.createObjectURL(clipBlob);
                    playback.classList.remove('hidden');
                    statusEl.textContent = 'Recording ready';
                };
                clipMediaRecorder.start();
                isRecording = true;
                recordBtn.textContent = 'Stop';
                recordBtn.classList.add('recording');
                statusEl.textContent = 'Recording...';
            } catch (e) {
                showToast('Microphone access denied', 'error');
            }
        }
    });

    document.getElementById('clipFile').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            clipBlob = file;
            playback.src = URL.createObjectURL(file);
            playback.classList.remove('hidden');
            statusEl.textContent = 'File loaded';
        }
    });

    translateBtn.addEventListener('click', async () => {
        if (!clipBlob) { showToast('Record or upload audio first', 'info'); return; }

        const target = document.getElementById('clipLang').value;
        translateBtn.classList.add('loading');
        translateBtn.textContent = 'Transcribing...';
        document.getElementById('clipResult').classList.add('hidden');
        showSkeleton('clipSkeleton');

        try {
            const form = new FormData();
            form.append('file', clipBlob, 'recording.webm');
            form.append('target', target);

            const res = await fetch('/api/translate-clip', { method: 'POST', body: form });
            const data = await res.json();

            if (data.error) {
                showToast(data.error, 'error');
            } else {
                document.getElementById('clipTranscript').textContent = data.transcript;
                document.getElementById('clipTranslation').textContent = data.translation;
                const clipRomanizedEl = document.getElementById('clipRomanized');
                if (data.romanized) {
                    clipRomanizedEl.textContent = data.romanized;
                    clipRomanizedEl.classList.remove('hidden');
                } else {
                    clipRomanizedEl.textContent = '';
                    clipRomanizedEl.classList.add('hidden');
                }
                document.getElementById('clipAudio').src = data.audio_url;
                document.getElementById('clipResult').classList.remove('hidden');
            }
        } catch (e) {
            showToast('Transcription failed: ' + e.message, 'error');
        }

        hideSkeleton('clipSkeleton');
        translateBtn.classList.remove('loading');
        translateBtn.textContent = 'Transcribe and Translate';
    });

    document.getElementById('clipCopyBtn').addEventListener('click', () => {
        const translation = document.getElementById('clipTranslation').textContent;
        const romanized = document.getElementById('clipRomanized').textContent;
        copyText(translation + (romanized ? '\n' + romanized : ''));
    });
    document.getElementById('clipDownloadBtn').addEventListener('click', () => {
        const transcript = document.getElementById('clipTranscript').textContent;
        const translation = document.getElementById('clipTranslation').textContent;
        const romanized = document.getElementById('clipRomanized').textContent;
        downloadText(`Transcript:\n${transcript}\n\nTranslation:\n${translation}` +
            (romanized ? `\n\nRomanized:\n${romanized}` : ''), 'clip-translation.txt');
    });
}

// === IMAGE/OCR TAB ===
function initOcrTab() {
    const fileInput = document.getElementById('ocrFile');
    const preview = document.getElementById('ocrPreview');
    const btn = document.getElementById('ocrTranslateBtn');

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            preview.src = URL.createObjectURL(file);
            preview.classList.remove('hidden');
        }
    });

    btn.addEventListener('click', async () => {
        if (!fileInput.files[0]) { showToast('Upload an image first', 'info'); return; }

        const target = document.getElementById('ocrLang').value;
        btn.classList.add('loading');
        btn.textContent = 'Processing...';
        document.getElementById('ocrResult').classList.add('hidden');
        showSkeleton('ocrSkeleton');

        try {
            const form = new FormData();
            form.append('file', fileInput.files[0]);
            form.append('target', target);

            const res = await fetch('/api/translate-ocr', { method: 'POST', body: form });
            const data = await res.json();

            if (data.error) {
                showToast(data.error, 'error');
            } else {
                document.getElementById('ocrExtracted').textContent = data.extracted_text;
                document.getElementById('ocrDetected').innerHTML = createLangBadge(data.detected_language);
                document.getElementById('ocrTranslation').textContent = data.translation;
                const ocrRomanizedEl = document.getElementById('ocrRomanized');
                if (data.romanized) {
                    ocrRomanizedEl.textContent = data.romanized;
                    ocrRomanizedEl.classList.remove('hidden');
                } else {
                    ocrRomanizedEl.textContent = '';
                    ocrRomanizedEl.classList.add('hidden');
                }
                document.getElementById('ocrAudio').src = data.audio_url;
                document.getElementById('ocrResult').classList.remove('hidden');
            }
        } catch (e) {
            showToast('OCR failed: ' + e.message, 'error');
        }

        hideSkeleton('ocrSkeleton');
        btn.classList.remove('loading');
        btn.textContent = 'Extract & Translate';
    });

    document.getElementById('ocrCopyBtn').addEventListener('click', () => {
        const translation = document.getElementById('ocrTranslation').textContent;
        const romanized = document.getElementById('ocrRomanized').textContent;
        copyText(translation + (romanized ? '\n' + romanized : ''));
    });
    document.getElementById('ocrDownloadBtn').addEventListener('click', () => {
        const extracted = document.getElementById('ocrExtracted').textContent;
        const translation = document.getElementById('ocrTranslation').textContent;
        const romanized = document.getElementById('ocrRomanized').textContent;
        downloadText(`Extracted text:\n${extracted}\n\nTranslation:\n${translation}` +
            (romanized ? `\n\nRomanized:\n${romanized}` : ''), 'ocr-translation.txt');
    });
}

// === LIVE TAB ===
let liveWs = null;
let liveMediaRecorder = null;
let liveStream = null;
let liveIsActive = false;

function initLiveTab() {
    const startBtn = document.getElementById('liveStartBtn');
    const clearBtn = document.getElementById('liveClearBtn');
    const copyBtn = document.getElementById('liveCopyBtn');
    const statusEl = document.getElementById('liveStatus');
    const transcriptEl = document.getElementById('liveTranscript');
    const translationEl = document.getElementById('liveTranslation');
    const romanizedEl = document.getElementById('liveRomanized');
    const langSelect = document.getElementById('liveLang');

    startBtn.addEventListener('click', () => {
        if (liveIsActive) { stopLive(); } else { startLive(); }
    });

    clearBtn.addEventListener('click', () => {
        transcriptEl.textContent = '';
        translationEl.textContent = '';
        romanizedEl.textContent = '';
        romanizedEl.classList.add('hidden');
        if (liveWs && liveWs.readyState === WebSocket.OPEN) {
            liveWs.send(JSON.stringify({ action: 'clear' }));
        }
    });

    copyBtn.addEventListener('click', () => {
        const text = transcriptEl.textContent + '\n\n' + translationEl.textContent;
        copyText(text);
    });

    document.getElementById('liveSummarizeBtn').addEventListener('click', async () => {
        const text = transcriptEl.textContent.trim();
        if (!text) { showToast('No transcript to summarize', 'info'); return; }

        try {
            const form = new FormData();
            form.append('text', text);
            const res = await fetch('/api/summarize', { method: 'POST', body: form });
            const data = await res.json();
            if (data.error) {
                showToast(data.error, 'error');
            } else {
                showToast('Summary: ' + data.summary, 'info');
            }
        } catch (e) {
            showToast('Summarization failed', 'error');
        }
    });

    langSelect.addEventListener('change', () => {
        if (liveWs && liveWs.readyState === WebSocket.OPEN) {
            liveWs.send(JSON.stringify({ target_lang: langSelect.value }));
        }
    });

    async function startLive() {
        statusEl.textContent = 'Connecting...';
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = protocol + '//' + window.location.host + '/ws/live';

        try {
            liveWs = new WebSocket(wsUrl);
        } catch (e) {
            statusEl.textContent = 'Connection failed';
            return;
        }

        liveWs.onopen = async () => {
            liveWs.send(JSON.stringify({ target_lang: langSelect.value }));

            try {
                liveStream = await navigator.mediaDevices.getUserMedia({
                    audio: { channelCount: 1, echoCancellation: true }
                });
            } catch (e) {
                showToast('Microphone access denied', 'error');
                liveWs.close();
                return;
            }

            liveIsActive = true;
            startBtn.textContent = 'Stop';
            startBtn.classList.add('recording');
            statusEl.textContent = 'Listening...';
            recordCycle();
        };

        function recordCycle() {
            if (!liveIsActive || !liveStream) return;

            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus' : 'audio/webm';

            liveMediaRecorder = new MediaRecorder(liveStream, { mimeType });
            let chunks = [];

            liveMediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) chunks.push(event.data);
            };

            liveMediaRecorder.onstop = () => {
                if (chunks.length > 0 && liveWs && liveWs.readyState === WebSocket.OPEN) {
                    const blob = new Blob(chunks, { type: mimeType });
                    liveWs.send(blob);
                }
                if (liveIsActive) recordCycle();
            };

            liveMediaRecorder.start();
            setTimeout(() => {
                if (liveMediaRecorder && liveMediaRecorder.state === 'recording') {
                    liveMediaRecorder.stop();
                }
            }, 2000);
        }

        liveWs.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.transcript) transcriptEl.textContent = data.transcript;
            if (data.translation) translationEl.textContent = data.translation;
            if (data.romanized) {
                romanizedEl.textContent = data.romanized;
                romanizedEl.classList.remove('hidden');
            }
            if (data.status === 'ok' || data.status === 'listening') {
                statusEl.textContent = 'Listening...';
            } else if (data.status === 'error') {
                statusEl.textContent = 'Error: ' + (data.message || '');
            } else if (data.status === 'cleared') {
                transcriptEl.textContent = '';
                translationEl.textContent = '';
                romanizedEl.textContent = '';
                romanizedEl.classList.add('hidden');
            }
        };

        liveWs.onerror = () => {
            showToast('WebSocket connection error', 'error');
            stopLive();
        };

        liveWs.onclose = () => {
            if (liveIsActive) {
                statusEl.textContent = 'Disconnected';
                stopLive();
            }
        };
    }

    function stopLive() {
        liveIsActive = false;
        if (liveMediaRecorder && liveMediaRecorder.state !== 'inactive') liveMediaRecorder.stop();
        if (liveStream) { liveStream.getTracks().forEach(t => t.stop()); liveStream = null; }
        if (liveWs) { liveWs.close(); liveWs = null; }
        startBtn.textContent = 'Start Listening';
        startBtn.classList.remove('recording');
        statusEl.textContent = 'Stopped';
    }
}
