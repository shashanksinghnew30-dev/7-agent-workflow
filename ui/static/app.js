// Client logic for 7-Agent Autonomous AI Workflow

let currentSessionId = null;
let eventSource = null;
let currentFiles = {};
let activeFileKey = null;

function setPrompt(text) {
  const input = document.getElementById("prompt-input");
  if (input) {
    input.value = text;
    input.focus();
  }
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-pane").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));

  const targetPane = document.getElementById(tabId);
  if (targetPane) targetPane.classList.add("active");

  const btn = Array.from(document.querySelectorAll(".tab-btn")).find(b => 
    b.getAttribute("onclick") && b.getAttribute("onclick").includes(tabId)
  );
  if (btn) btn.classList.add("active");
}

function initEventStream() {
  if (eventSource) {
    eventSource.close();
  }

  eventSource = new EventSource("/api/stream");

  eventSource.onopen = () => {
    document.getElementById("global-status-text").innerText = "Stream Connected";
  };

  eventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      handleAgentEvent(data);
    } catch (err) {
      console.error("Failed to parse SSE event:", err);
    }
  };

  eventSource.onerror = (err) => {
    document.getElementById("global-status-text").innerText = "Reconnecting...";
  };
}

function handleAgentEvent(evt) {
  const { agent, event_type, message, payload, timestamp } = evt;

  // Append to terminal feed
  appendLogEntry(agent, message, timestamp);

  // Update DAG node state
  updateDagHighlights(agent, event_type, message, payload);

  // Dispatch specific payloads
  if (event_type === "debate") {
    appendDebateTurn(payload);
  } else if (event_type === "code" && payload.path && payload.content) {
    currentFiles[payload.path] = payload.content;
    renderFileTabs();
  } else if (event_type === "qa") {
    updateQADisplay(payload, message);
  } else if (event_type === "supervisor") {
    updateSupervisorDisplay(payload);
  } else if (event_type === "delivery") {
    updateDeliveryDisplay(payload);
  }
}

function appendLogEntry(agent, message, timestamp) {
  const feed = document.getElementById("terminal-feed");
  const row = document.createElement("div");
  row.className = "log-entry";

  const timeStr = timestamp ? new Date(timestamp * 1000).toLocaleTimeString() : "";
  row.innerHTML = `
    <span class="log-time">[${timeStr}]</span>
    <span class="log-agent">${escapeHtml(agent)}:</span>
    <span class="log-msg">${escapeHtml(message)}</span>
  `;
  feed.appendChild(row);
  feed.scrollTop = feed.scrollHeight;
}

function updateDagHighlights(agent, event_type, message, payload) {
  const clearActive = () => {
    for (let i = 1; i <= 7; i++) {
      const node = document.getElementById(`node-${i}`);
      if (node) node.classList.remove("active");
    }
  };

  if (agent.includes("Agent 1")) {
    clearActive();
    setNodeState("node-1", "active");
  } else if (agent.includes("Agent 2") || agent.includes("Agent 3") || agent.includes("Interpreter") || agent.includes("Architect")) {
    setNodeState("node-1", "completed");
    setNodeState("node-2", "active");
  } else if (agent.includes("Agent 4") || agent.includes("Lead Coder")) {
    setNodeState("node-2", "completed");
    setNodeState("node-4", "active");
  } else if (agent.includes("Agent 5") || agent.includes("Strict QA")) {
    if (message.includes("DEFECT") || message.includes("Looping back") || message.includes("FAILED")) {
      const node5 = document.getElementById("node-5");
      if (node5) node5.classList.add("loopback");
      const badge = document.getElementById("badge-loop");
      if (badge) {
        badge.style.display = "inline-block";
        badge.innerText = `Loopback -> Coder`;
      }
    } else if (message.includes("PASSED")) {
      setNodeState("node-4", "completed");
      setNodeState("node-5", "completed");
    } else {
      setNodeState("node-5", "active");
    }
  } else if (agent.includes("Agent 6") || agent.includes("Supervisor")) {
    setNodeState("node-5", "completed");
    setNodeState("node-6", "active");
  } else if (agent.includes("Agent 7") || agent.includes("Delivery")) {
    setNodeState("node-6", "completed");
    setNodeState("node-7", "completed");
    document.getElementById("global-status-text").innerText = "Release Delivered";
  }
}

function setNodeState(nodeId, state) {
  const el = document.getElementById(nodeId);
  if (!el) return;
  el.classList.remove("active", "completed", "loopback");
  el.classList.add(state);
}

function appendDebateTurn(turn) {
  const container = document.getElementById("debate-container");
  if (!container) return;

  if (container.querySelector("p")) {
    container.innerHTML = "";
  }

  const isInterpreter = turn.speaker.includes("Agent 2") || turn.speaker.includes("Interpreter");
  const card = document.createElement("div");
  card.className = `debate-card ${isInterpreter ? "interpreter" : "architect"}`;

  let tradeOffsHtml = "";
  if (turn.trade_offs && turn.trade_offs.length > 0) {
    tradeOffsHtml = `<div class="tradeoff-tags">${turn.trade_offs.map(t => `<span class="tradeoff-tag">${escapeHtml(t)}</span>`).join("")}</div>`;
  }

  card.innerHTML = `
    <div class="debate-speaker">${escapeHtml(turn.speaker)} • Round ${turn.round_number}</div>
    <div class="debate-content">${escapeHtml(turn.thesis)}</div>
    ${tradeOffsHtml}
  `;
  container.appendChild(card);
}

function renderFileTabs() {
  const tabsContainer = document.getElementById("code-file-tabs");
  if (!tabsContainer) return;

  tabsContainer.innerHTML = "";
  const paths = Object.keys(currentFiles);
  if (paths.length === 0) return;

  if (!activeFileKey || !currentFiles[activeFileKey]) {
    activeFileKey = paths[0];
  }

  paths.forEach(p => {
    const btn = document.createElement("button");
    btn.className = `file-tab ${p === activeFileKey ? "active" : ""}`;
    btn.innerText = p;
    btn.onclick = () => {
      activeFileKey = p;
      renderFileTabs();
      displayCurrentCode();
    };
    tabsContainer.appendChild(btn);
  });

  displayCurrentCode();
}

function displayCurrentCode() {
  const pre = document.getElementById("code-display");
  if (pre && activeFileKey && currentFiles[activeFileKey]) {
    pre.innerText = currentFiles[activeFileKey];
  }
}

function copyCurrentCode() {
  if (activeFileKey && currentFiles[activeFileKey]) {
    navigator.clipboard.writeText(currentFiles[activeFileKey]).then(() => {
      alert(`Copied ${activeFileKey} to clipboard!`);
    });
  }
}

function updateQADisplay(payload, msg) {
  if (payload.report) {
    payload = payload.report;
  }

  const statusVal = document.getElementById("qa-status-val");
  const testsVal = document.getElementById("qa-tests-val");
  const loopsVal = document.getElementById("qa-loops-val");
  const execLog = document.getElementById("qa-exec-log");

  if (payload.passed !== undefined) {
    statusVal.innerText = payload.passed ? "PASSED" : "DEFECT FOUND";
    statusVal.style.color = payload.passed ? "var(--accent-green)" : "var(--accent-red)";
  }

  if (payload.tests_executed !== undefined) {
    testsVal.innerText = `${payload.tests_passed || 0} / ${payload.tests_executed || 0}`;
  }

  if (payload.loop_iteration !== undefined) {
    loopsVal.innerText = payload.loop_iteration;
  }

  if (payload.execution_stdout || payload.execution_stderr) {
    execLog.innerText = (payload.execution_stdout || "") + "\n" + (payload.execution_stderr || "");
  }
}

function updateSupervisorDisplay(payload) {
  const scoreVal = document.getElementById("sup-score-val");
  const verdictVal = document.getElementById("sup-verdict-val");
  const checklist = document.getElementById("sup-checklist");

  if (payload.alignment_score) {
    scoreVal.innerText = `${payload.alignment_score}%`;
    scoreVal.style.color = payload.alignment_score >= 85 ? "var(--accent-green)" : "var(--accent-yellow)";
  }

  if (payload.executive_verdict) {
    verdictVal.innerText = payload.executive_verdict;
    verdictVal.style.color = "var(--primary)";
  }

  if (payload.original_intent_checklist) {
    checklist.innerHTML = Object.entries(payload.original_intent_checklist).map(([k, v]) => `
      <li style="color: ${v ? 'var(--accent-green)' : 'var(--accent-red)'};">
        ${v ? '✔' : '✖'} ${escapeHtml(k)}
      </li>
    `).join("");
  }
}

function updateDeliveryDisplay(payload) {
  const container = document.getElementById("delivery-details");
  if (!container) return;

  const downloadUrl = `/api/download/${payload.project_slug || currentSessionId}`;

  container.innerHTML = `
    <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid var(--accent-green); border-radius: 8px; padding: 1.25rem;">
      <h3 style="color: var(--accent-green); font-size: 1.1rem; margin-bottom: 0.5rem;">Package Verified & Delivered</h3>
      <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1rem;">
        Generated ${payload.file_count || 0} production files (${payload.total_loc || 0} Lines of Code) with complete unit tests and documentation.
      </p>
      <div style="display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1rem;">
        <a href="${downloadUrl}" class="btn-download" download>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
          Download Package ZIP
        </a>
      </div>
      <div style="font-family: var(--font-mono); font-size: 0.8rem; background: #05080f; padding: 0.75rem; border-radius: 6px; border: 1px solid var(--border-color);">
        <span style="color: var(--text-muted);">Quickstart: </span><span style="color: var(--primary);">${escapeHtml(payload.quickstart_command || "python run.py")}</span><br>
        <span style="color: var(--text-muted);">Run Tests: </span><span style="color: var(--primary);">${escapeHtml(payload.test_command || "python -m unittest discover -s tests")}</span>
      </div>
    </div>
  `;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

document.addEventListener("DOMContentLoaded", () => {
  initEventStream();

  const form = document.getElementById("workflow-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const promptInput = document.getElementById("prompt-input");
    const checkLoopback = document.getElementById("check-loopback");
    const promptText = promptInput.value.trim();

    if (!promptText) return;

    // Reset UI state
    currentFiles = {};
    activeFileKey = null;
    document.getElementById("debate-container").innerHTML = '<p style="color: var(--text-muted); font-size: 0.9rem;">Agents initiating debate...</p>';
    document.getElementById("code-file-tabs").innerHTML = "";
    document.getElementById("code-display").innerText = "Generating code...";
    document.getElementById("badge-loop").style.display = "none";

    const runBtn = document.getElementById("btn-run");
    runBtn.disabled = true;
    runBtn.style.opacity = "0.6";

    try {
      const resp = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: promptText,
          demo_loopback: checkLoopback.checked
        })
      });
      const data = await resp.json();
      currentSessionId = data.session_id;
    } catch (err) {
      alert("Error starting workflow: " + err);
    } finally {
      runBtn.disabled = false;
      runBtn.style.opacity = "1";
    }
  });
});
