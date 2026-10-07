document.getElementById('analyze-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const caseInput = document.getElementById('case-input').value;
    if (!caseInput.trim()) return;

    // UI States
    const btn = document.getElementById('submit-btn');
    const spinner = document.getElementById('loading-spinner');
    const btnText = btn.querySelector('.btn-text');
    const resultsSection = document.getElementById('results-section');
    
    btn.disabled = true;
    spinner.classList.remove('hidden');
    btnText.textContent = 'Analyzing...';
    resultsSection.classList.add('hidden');

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ case_text: caseInput })
        });

        if (!response.ok) throw new Error('Analysis failed');

        const data = await response.json();
        renderResults(data);
    } catch (error) {
        console.error(error);
        alert('An error occurred during analysis.');
    } finally {
        btn.disabled = false;
        spinner.classList.add('hidden');
        btnText.textContent = 'Analyze Case';
    }
});

function renderResults(data) {
    // Show sections
    document.getElementById('results-section').classList.remove('hidden');
    
    // 1. Render Patient Context (Sidebar)
    const ctx = data.patient_context;
    const ctxContainer = document.getElementById('patient-context');
    ctxContainer.innerHTML = '';
    ctxContainer.classList.remove('empty-state');

    const addTags = (title, items, type) => {
        if (!items || items.length === 0) return;
        const wrapper = document.createElement('div');
        wrapper.style.marginBottom = '1rem';
        wrapper.innerHTML = `<div style="font-size:0.8rem; color:#94a3b8; margin-bottom:0.3rem;">${title}</div>`;
        items.forEach(item => {
            const span = document.createElement('span');
            span.className = `context-item ${type}`;
            span.textContent = item.text || item.normalized_name;
            wrapper.appendChild(span);
        });
        ctxContainer.appendChild(wrapper);
    };

    if (ctx.age || ctx.sex) {
        const demo = document.createElement('div');
        demo.className = 'context-item';
        demo.style.background = 'rgba(255,255,255,0.1)';
        demo.textContent = `${ctx.age || '?'} yo ${ctx.sex || 'Unknown'}`;
        ctxContainer.appendChild(demo);
    }

    addTags('Symptoms', ctx.symptoms, 'symptom');
    addTags('Conditions', ctx.known_conditions, 'condition');
    addTags('Medications', ctx.medications, 'medication');

    // 2. Render Missing Info (Sidebar)
    const missingList = document.getElementById('missing-info-list');
    missingList.innerHTML = '';
    const report = data.report || {};
    const missing = report.missing_information || [];
    if (missing.length > 0) {
        missing.forEach(m => {
            const li = document.createElement('li');
            li.textContent = m;
            missingList.appendChild(li);
        });
    } else {
        missingList.innerHTML = '<li>None detected.</li>';
    }

    // 3. Render Diagnoses (Main)
    const diagContainer = document.getElementById('diagnoses-container');
    diagContainer.innerHTML = '';
    const diagnoses = report.ranked_diagnoses || [];

    if (diagnoses.length === 0) {
        diagContainer.innerHTML = '<div class="glass-panel" style="padding:2rem; text-align:center;">No differential diagnoses could be generated.</div>';
    } else {
        diagnoses.forEach((d, index) => {
            const card = document.createElement('div');
            card.className = 'diag-card glass-panel animate-up';
            card.style.animationDelay = `${index * 0.1}s`;

            // Confidence class
            let confClass = 'conf-low';
            if (d.confidence >= 0.75) confClass = 'conf-high';
            else if (d.confidence >= 0.5) confClass = 'conf-med';

            let safetyHtml = '';
            if (d.safety_notes && d.safety_notes.length > 0) {
                d.safety_notes.forEach(note => {
                    safetyHtml += `<div class="safety-note">⚠️ ${note}</div>`;
                });
            }

            let treatmentsHtml = '';
            if (d.treatment_considerations && d.treatment_considerations.length > 0) {
                treatmentsHtml = `<h4>Treatment Considerations</h4><ul class="list-items">`;
                d.treatment_considerations.forEach(t => treatmentsHtml += `<li>${t}</li>`);
                treatmentsHtml += `</ul>`;
            }

            card.innerHTML = `
                <div class="diag-header">
                    <div class="diag-title">${d.diagnosis}</div>
                    <div class="conf-badge ${confClass}">${(d.confidence * 100).toFixed(0)}% Conf</div>
                </div>
                <div class="diag-body">
                    ${treatmentsHtml}
                    ${safetyHtml}
                </div>
            `;
            diagContainer.appendChild(card);
        });
    }

    // 4. Render Investigations
    const invPanel = document.getElementById('investigations-panel');
    const invList = document.getElementById('investigations-list');
    invList.innerHTML = '';
    
    // We get investigations from the top diagnosis, or merge them. For simplicity, grab from first.
    let invs = [];
    if (diagnoses.length > 0 && diagnoses[0].recommended_tests) {
        invs = diagnoses[0].recommended_tests;
    }
    
    if (invs.length > 0) {
        invPanel.classList.remove('hidden');
        invs.forEach(inv => {
            const li = document.createElement('li');
            li.textContent = inv;
            invList.appendChild(li);
        });
    } else {
        invPanel.classList.add('hidden');
    }

    // 5. Disclaimer
    document.getElementById('report-disclaimer').textContent = report.disclaimer || "This is a research prototype.";
}
