let summaryTable = null, dataTable = null, brandFormsTable = null;

// setup chart plugins
Chart.register(ChartDataLabels);

// base palette from user + expanded complementary pastels
const colors = {
    cats: { 'cars': '#b3cde0', 'luxury clothes': '#fbb4ae', 'other': '#d9d9d9', 'social media': '#ccebc5', 'electronics': '#decbe4', 'alcohol and smoke': '#fed9a6', 'food': '#e5d8bd', 'persons': '#fddaec', 'weapons': '#b3e2cd', 'places': '#fdcdac' },
    pastels: ['#b3cde0','#fbb4ae','#ccebc5','#decbe4','#fed9a6','#e5d8bd','#fddaec','#b3e2cd','#fdcdac','#cbd5e8','#f4cae4','#e6f5c9','#fff2ae','#f1e2cc','#f1b6da','#b8e186']
};

// standard bar chart config
const baseConfig = {
    responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false },
    scales: { 
        x: { stacked: true, grid: { display: false }, ticks: { font: { family: "'Inter', sans-serif" }, color: '#64748b', callback: function(v) { const l = parseInt(this.getLabelForValue(v)); return l % 2 !== 0 ? l : ''; }}}, 
        y: { stacked: true, border: { display: false }, grid: { color: '#f1f5f9' }, ticks: { font: { family: "'Inter', sans-serif" }, color: '#64748b' }} 
    },
    plugins: { 
        datalabels: { display: false },
        legend: { position: 'top', reverse: true, labels: { usePointStyle: false, boxWidth: 14, boxHeight: 14, useBorderRadius: true, borderRadius: 4, font: { family: "'Inter', sans-serif", size: 12 }, color: '#475569', padding: 15 }},
        tooltip: { backgroundColor: 'rgba(255, 255, 255, 0.95)', titleColor: '#0f172a', bodyColor: '#334155', borderColor: '#e2e8f0', borderWidth: 1, padding: 12, cornerRadius: 6, displayColors: true, itemSort: (a, b) => b.raw - a.raw }
    }
};

// restored standalone config for the mtld chart
const simpleBarConfig = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
        x: { grid: { display: false }, ticks: { font: { family: "'Inter', sans-serif" }, color: '#64748b' } },
        y: { beginAtZero: true, border: { display: false }, grid: { color: '#f1f5f9' }, ticks: { font: { family: "'Inter', sans-serif" }, color: '#64748b' } }
    },
    plugins: {
        legend: { display: false },
        tooltip: baseConfig.plugins.tooltip,
        datalabels: { display: false }
    }
};

const getOriginTag = o => {
    const l = (o||'').toLowerCase();
    return l.includes('western') || l.includes('abroad') ? 'WST' : l.includes('domestic') ? 'DOM' : l.includes('cis') ? 'CIS' : 'UNK';
};

const escapeHTML = str => String(str||'').replace(/[&<>'"]/g, t => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[t] || t));

function applyColors(datasets, isCat = false) {
    let rank = 0;
    return datasets.reverse().map(ds => {
        const l = (ds.label || '').toLowerCase();
        ds.backgroundColor = isCat && colors.cats[l] ? colors.cats[l] : l === 'other' ? '#d9d9d9' : colors.pastels[rank++ % colors.pastels.length];
        ds.borderWidth = 0; ds.borderRadius = 2; ds.barPercentage = 0.7;
        return ds;
    }).reverse();
}

const updateChart = (id, type, data, opts) => {
    const chartInstance = Chart.getChart(id);
    if (chartInstance) chartInstance.destroy();
    if (data && (!data.datasets || data.datasets.length)) {
        new Chart(document.getElementById(id), { type, data, options: opts });
    }
};

const renderRangePlot = (parsed, globalMax) => {
    if (!parsed) return '0';
    const { min, med, max } = parsed;
    const pct = v => (v / globalMax) * 100;
    return `
        <div style="display:flex;flex-direction:column;gap:6px;width:140px" title="Min: ${min} | Med: ${med} | Max: ${max}">
            <div style="display:flex;justify-content:space-between;align-items:flex-end;font-size:10px;line-height:1;font-variant-numeric:tabular-nums">
                <span style="color:#94a3b8">${min}</span><span style="color:#334155;font-weight:600;font-size:11px">${med}</span><span style="color:#94a3b8">${max}</span>
            </div>
            <div style="width:100%;height:3px;background:#f1f5f9;border-radius:2px;position:relative">
                <div style="position:absolute;left:${pct(min)}%;width:${pct(max)-pct(min)}%;height:100%;background:#cbd5e1;border-radius:2px"></div>
                <div style="position:absolute;left:${pct(med)}%;top:50%;width:7px;height:7px;background:#475569;border-radius:50%;transform:translate(-50%,-50%);box-shadow:0 0 0 1.5px #fff"></div>
            </div>
        </div>`;
};

async function updateData() {
    const q = ['genre', 'platform', 'brand', 'category', 'origin'].map(f => `${f}=${document.getElementById(f+'Filter').value}`).join('&');
    const res = await fetch(`/api/data?${q}`);
    const data = await res.json();
    
    // Bar Charts
    updateChart('categoryChart', 'bar', { labels: data.graph3.years, datasets: applyColors(data.graph3.datasets, true) }, baseConfig);
    updateChart('genreChart', 'bar', { labels: data.graph2.years, datasets: applyColors(data.graph2.datasets) }, baseConfig);
    updateChart('brandsChart', 'bar', { labels: data.graph1.years, datasets: applyColors(data.graph1.datasets) }, baseConfig);
    
    // Line Charts
    const lineOpts = { 
        ...baseConfig, 
        scales: { 
            x: { ...baseConfig.scales.x, stacked: false, grid: { display: false } }, 
            y: { ...baseConfig.scales.y, stacked: false, beginAtZero: true, max: 50, border: { display: false }, grid: { display: true, color: '#f1f5f9' } }
        }, 
        plugins: { 
            ...baseConfig.plugins, 
            legend: { display: false }, 
            tooltip: { 
                ...baseConfig.plugins.tooltip, 
                callbacks: { afterBody: c => { const ds = c[0].dataset; return ds.topBrands?.[c[0].dataIndex]?.length ? ['', 'Top 3:', ...ds.topBrands[c[0].dataIndex].map(b => '• ' + b)] : []; }}
            }, 
            datalabels: { 
                display: c => c.dataIndex % 3 === 0 || c.dataIndex === c.chart.data.labels.length - 1, align: 'top', offset: 4, color: '#475569', font: { family: "'Inter'", size: 10, weight: '600' }, formatter: v => v ? v + '%' : '' 
            }
        }
    };
    
    ['ratioChart', 'westernRatioChart', 'domesticRatioChart'].forEach((id, i) => {
        const chartData = data[`graph${i+4}`];
        updateChart(id, 'line', { labels: chartData.years, datasets: chartData.datasets }, lineOpts);
    });
    
    // MTLD Chart
    if (data.graph7?.labels) {
        data.graph7.datasets[0] = { ...data.graph7.datasets[0], backgroundColor: data.graph7.labels.map((_, i) => colors.pastels[i % colors.pastels.length]), borderRadius: 2, barPercentage: 0.7 };
        updateChart('mtldChart', 'bar', data.graph7, simpleBarConfig); 
    }

    // Tables logic parsing
    let maxC = 0, maxW = 0, maxSongs = 0;
    (data.summary_data || []).forEach(r => {
        const c = r.chars_stats.split(' / ').map(Number), w = r.words_stats.split(' / ').map(Number);
        r._cp = { min: c[0], med: c[1], max: c[2] }; r._wp = { min: w[0], med: w[1], max: w[2] };
        maxC = Math.max(maxC, c[2]); maxW = Math.max(maxW, w[2]);
    });
    (data.brand_forms_data || []).forEach(r => { maxSongs = Math.max(maxSongs, r.total_songs); });

    const initTable = (table, id, tData, cols, order, opts={}) => {
        if (table) { table.clear(); table.rows.add(tData); table.draw(); return table; }
        
        const defaultOpts = {
            data: tData, 
            order, 
            columns: cols, 
            dom: '<"dt-top"lfB>rt<"dt-bottom"ip><"clear">', 
            buttons: [
                {
                    extend: 'csvHtml5',
                    // Button configuration updated to just display the SVG icon, with a tooltip for functionality indication
                    text: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>',
                    titleAttr: 'Download CSV',
                    className: 'dt-button'
                }
            ],
            language: { search: "", searchPlaceholder: "Search records...", info: "Showing _START_ to _END_ of _TOTAL_ entries", infoEmpty: "No entries found" }
        };
        
        return $(id).DataTable({ ...defaultOpts, ...opts });
    };

    summaryTable = initTable(summaryTable, '#summaryTable', data.summary_data, [
        { data: 'genre' }, { data: 'total_songs' }, { data: 'total_mentions' }, { data: 'mentions_percent' },
        { data: 'chars_stats', render: (d, t, r) => t === 'display' ? renderRangePlot(r._cp, maxC) : r._cp?.med },
        { data: 'words_stats', render: (d, t, r) => t === 'display' ? renderRangePlot(r._wp, maxW) : r._wp?.med }
    ], [[1, 'desc']], { paging: false, info: false, searching: false, dom: 'rt' });

    brandFormsTable = initTable(brandFormsTable, '#brandFormsTable', data.brand_forms_data, [
        { data: 'brand', render: d => `<span style="font-weight:600;color:#0f172a;font-size:14px;">${d}</span>` }, 
        { data: 'total_songs', render: (d, t, row) => {
            if (t !== 'display') return d;
            const pct = (d / maxSongs) * 100;
            const catColor = colors.cats[row.category] || '#94a3b8';
            return `
                <div style="display:flex;align-items:center;gap:8px;width:100%;">
                    <span style="color:#334155;font-weight:600;font-variant-numeric:tabular-nums;width:30px;">${d}</span>
                    <div style="flex-grow:1;height:6px;background:#f1f5f9;border-radius:3px;overflow:hidden;max-width:140px;">
                        <div style="width:${pct}%;height:100%;background:${catColor};border-radius:3px;"></div>
                    </div>
                </div>`;
        }},
        { data: 'top_forms', orderable: false, render: (d, t, row) => {
            if (t === 'filter') return Array.isArray(d) ? d.map(f => f.form).join(' ') : '';
            if (!Array.isArray(d) || !d.length) return '<span style="color:#94a3b8;font-style:italic">none</span>';
            
            const catColor = colors.cats[row.category] || '#e2e8f0'; 
            
            return `<div style="display:flex;flex-wrap:wrap;gap:6px">${d.map(f => `
                <div style="display:inline-flex;align-items:center;gap:6px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:4px 8px;font-size:12px;">
                    <span style="color:#475569;font-family:ui-monospace,SFMono-Regular,monospace;">"${f.form}"</span>
                    <span style="background:${catColor};color:rgba(30,41,59,0.65);border-radius:6px;padding:2px 8px;font-size:10px;font-weight:600;min-width:22px;text-align:center;">${f.count}</span>
                </div>`).join('')}</div>`;
        }}
    ], [[1, 'desc']], { pageLength: 10, lengthMenu: [5, 10, 25, 50] });

    dataTable = initTable(dataTable, '#songTable', data.table_data, [
        { data: 'year' }, { data: 'platform' }, { data: 'matched_artist' }, { data: 'matched_song' }, { data: 'chosen_genre' },
        { data: 'extracted_brands', orderable: false, render: (d, t) => {
            if (t === 'filter') return Array.isArray(d) ? d.map(b => `${b.normalized||''} ${b.mention||''} ${b.category||''}`).join(' ') : d;
            if (!Array.isArray(d) || !d.length) return '<span style="color:#94a3b8;font-style:italic">none</span>';
            
            return `<div style="display:flex;flex-wrap:wrap;gap:8px">${d.map(b => {
                const catColor = colors.cats[(b.category||'').toLowerCase()] || '#e2e8f0';
                return `
                <div style="display:inline-flex;align-items:center;gap:6px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:4px 8px;font-size:12px;width:fit-content;">
                    <span style="color:#475569;font-family:ui-monospace,SFMono-Regular,monospace;">"${b.mention||'?'}"</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="2"><path d="M5 12h14"></path><path d="m12 5 7 7-7 7"></path></svg>
                    <span style="font-weight:600;color:#0f172a;">${b.normalized||b.mention}</span>
                    <span style="background:${catColor};color:rgba(30,41,59,0.65);padding:2px 6px;border-radius:6px;font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">${b.category||'other'}</span>
                    <span style="background:#cbd5e1;color:rgba(30,41,59,0.65);padding:2px 6px;border-radius:6px;font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">${getOriginTag(b.origin)}</span>
                </div>`
            }).join('')}</div>`;
        }},
        { data: 'lyrics', orderable: false, render: (v, t) => t === 'display' ? `<button class="view-btn">View</button>` : v }
    ], [[0, 'desc']], { pageLength: 10 });

    $('#songTable tbody').off('click').on('click', '.view-btn', function() {
        const r = dataTable.row($(this).closest('tr')).data();
        let html = escapeHTML(r.lyrics);
        if (r.extracted_brands?.length) {
            const regex = new RegExp(`(${[...new Set(r.extracted_brands.map(b => escapeHTML(b.mention)).filter(Boolean).sort((a, b) => b.length - a.length))].join('|')})`, 'gi');
            html = html.replace(regex, '<span class="highlighted-mention">$1</span>');
        }
        $('#modalTitle').text(`${r.matched_artist} - ${r.matched_song}`);
        $('#modalLyrics').html(html);
        $('#lyricsModal').addClass('show');
    });
}

['genre', 'platform', 'brand', 'category', 'origin'].forEach(f => document.getElementById(f+'Filter').addEventListener('change', updateData));
$('#closeModal, #lyricsModal').on('click', e => { if (e.target.id === 'lyricsModal' || e.target.id === 'closeModal') $('#lyricsModal').removeClass('show'); });
document.addEventListener('DOMContentLoaded', updateData);