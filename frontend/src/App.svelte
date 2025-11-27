<script>
  import { onMount, tick } from 'svelte';
  import Chart from 'chart.js/auto';
  import { io } from 'socket.io-client';
  import { Play, Square, ImageDown, FileDown, HardDriveDownload, Radio } from 'lucide-svelte';
  import { showToast } from './lib/toast.js';
  import Toasts from './lib/Toasts.svelte';
  
  let charts = [];
  let canvasContainers = [];
  let metrics = [];
  let socket;

  let trainingInProgress = false;
  let loggedIn = false;

  let username = '';
  let password = '';

  let startTime = null;
  let elapsedTime = '00:00:00';
  let timerInterval;

  let previousRuns = []
  let runTitle = '';
  let runDescription = '';

  let showSaveModal = false;

  let currentRunId = null;

  function openSaveModal() {
    showSaveModal = true;
  }
  function closeSaveModal() {
    showSaveModal = false;
  }

  onMount(() => {
    initialize();

    return () => {
      destroyCharts();
      disconnectSocket();
    };
  });

  $: {
    if (loggedIn && currentRunId === null) {
      initSocketAndChart();
    } else if (loggedIn && currentRunId != null) {
      initChartForRunId(currentRunId);
    }
  }

  function disconnectSocket() {
    if (socket) {
      socket.off('status');
      socket.off('history');
      socket.off('update');
      socket.disconnect();
      socket = null;
    }
  }

  function destroyCharts() {
    if (charts) {
      charts.forEach(
        (chart) => {
          if (chart) chart.destroy();
        }
      )
      charts = [];
    }
    canvasContainers = [];
  }

  async function initialize() {
    try {
      const res = await fetch('/api/status', { method: "GET", credentials: 'include' });
      const data = await res.json();
      loggedIn = data.loggedIn;
      if (loggedIn) {
        await tick();
        initSocketAndChart();
        fetchRuns();
      }
    } catch (error) {
      console.error("Error checking login status:", error);
    }
  }

  function initSocketAndChart() {
    
    destroyCharts();
    disconnectSocket();

    socket = io(window.location.origin);

    socket.on('status', (status) => {
      console.log("Status received:", status);
      trainingInProgress = status.training

      if (trainingInProgress && status.start_time) {
        startTime = status.start_time;
        startTimer();
      } else {
        stopTimer();
      }
    })

    socket.on('history', (history) => {
      (async () => {
        try {
          console.log("History received:", history);
          const metricArr = extractMetrics(history);
          await setupCharts(metricArr);
          updateChartsWithHistory(history);
        } catch (err) {
          console.error("Failed to process history:", err);
        }
      })();
    });

    socket.on('update', data => {
      console.log("Update received:", data);
      updateChartsOnce(data);
    });
  }

  async function setupCharts(metricArr) {
    destroyCharts();

    metrics = metricArr

    canvasContainers = metrics.map(() => null);

    await tick();

    charts = metrics.map((metric, i) => {
      const ctx = canvasContainers[i].getContext("2d");
      return new Chart(ctx, {
        type: "line",
        data: { labels: [], datasets: [{ label: metric, data: [], borderColor: 'red', fill: false}] },
        options: {
          responsive: true,
          scales: {
            x: {
                title: { display: true, text: 'Epoch' },
                beginAtZero: true
            },
            y: {
                title: { display: true, text: metric },
                beginAtZero: true
            }
          }
        }
      });
    });
  }

  function updateChartsOnce(data) {
    charts.forEach((chart, i) => {
      chart.data.labels.push(data.epoch);
      chart.data.datasets[0].data.push(data[metrics[i]]);
      chart.update();
    });
  }

  function updateChartsWithHistory(history) {
    charts.forEach((chart, i) => {
      chart.data.labels = history.map(p => p.epoch);
      chart.data.datasets[0].data = history.map(p => p[metrics[i]]);
      chart.update();
    });
  }

  async function initChartForRunId(runId) {
    if (!runId) return;

    destroyCharts();
    disconnectSocket();

    stopTimer();
    
    const runData = await fetch(`/api/runs/${runId}`, { method: "GET", credentials: 'include' })
      .then(res => res.json())
      .then(json => json.run)
      .catch(err => {
        console.error("Failed to fetch run:", err);
        showToast("Failed to load run", "error");
        return;
      }
    );

    const history = runData.training_history

    await tick();
    
    await setupCharts(extractMetrics(history));
    updateChartsWithHistory(history);
  }

  async function login() {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
        credentials: 'include'
      });

      const data = await response.json();
      if (response.ok && data.success) {
        loggedIn = true;
        showToast("Login successful!", "success");
      } else {
        loggedIn = false;
        showToast("Login failed!", "error");
      }
    } catch (err) {
      console.error("Login error:", err);
      showToast("Login error!", "error");
    }
  }

  function extractMetrics(training_history) {
    if (!training_history || training_history.length === 0) return [];

    // use epoch as main key (x value)
    const keys = Object.keys(training_history[0]).filter(
      key => key !== "epoch"
    );
    
    // return array of keys
    return keys;
  }


  async function startTraining() {
    const response = await fetch('/api/start', { method: 'POST', credentials: 'include' });
    if (!response.ok) {
      showToast("Failed to start training!", "error");
      return;
    }

    // clear existing chart data
    destroyCharts();

    showToast("Training started!", "info");
  }
  async function stopTraining() {
    const response = await fetch('/api/stop', { method: 'POST', credentials: 'include' });
    if (!response.ok) {
      showToast("Failed to stop training!", "error");
      return;
    }

    showToast("Training stopped!", "info");
  }

  function downloadChart() {
    if (!charts) return;
    // loop through all charts
    charts.forEach((chart, i) => {
      const link = document.createElement('a');
      link.href = chart.toBase64Image();
      link.download = `experiment_${Date.now()}_${metrics[i]}.png`;
      link.click();
    });
  }

  function downloadCSV() {
    if (!charts || charts.length === 0) return;

    // Build header row: Epoch + all metrics
    const header = ["Epoch", ...metrics];

    // Determine number of epochs (assume all charts have same labels)
    const numRows = charts[0].data.labels.length;

    // Build CSV rows
    const rows = [];
    for (let i = 0; i < numRows; i++) {
      const row = [charts[0].data.labels[i]]; // Epoch
      charts.forEach((chart) => {
        row.push(chart.data.datasets[0].data[i]);
      });
      rows.push(row);
    }

    // Combine header + rows
    const csvContent = "data:text/csv;charset=utf-8," 
      + [header, ...rows].map(r => r.join(",")).join("\n");

    // Trigger download
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.href = encodedUri;
    link.download = `experiment_${Date.now()}.csv`;
    link.click();
  }


  function updateTrainingDuration() {
    if (!startTime) return;

    const diff = Date.now() - startTime;
    const hours = String(Math.floor(diff / 3600000)).padStart(2, "0");
    const minutes = String(Math.floor((diff % 3600000) / 60000)).padStart(2, "0");
    const seconds = String(Math.floor((diff % 60000) / 1000)).padStart(2, "0");

    elapsedTime = `${hours}:${minutes}:${seconds}`;
  }

  function startTimer() {
    if (timerInterval) return;
    timerInterval = setInterval(updateTrainingDuration, 1000);
  }

  function stopTimer() {
    clearInterval(timerInterval);
    timerInterval = null;
    startTime = null;
    elapsedTime = "00:00:00";
  }

  async function fetchRuns() {
    try {
      const res = await fetch('/api/runs', { method: "GET", credentials: 'include' });
      const data = await res.json();
      previousRuns = data.runs || [];
      console.log("Fetched runs: ", previousRuns);
    } catch (error) {
      console.error("Error fetching runs:", error);
      return [];
    }
  }

  async function saveRun() {
    try {
      const res = await fetch('/api/runs', {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ "title": runTitle, "description": runDescription })
      });
      const data = await res.json();
      if (data.success) {
        showToast("Run saved successfully!", "success");
      } else {
        showToast("Failed to save run!", "error");
      }
    } catch (error) {
      console.error("Error saving run:", error);
      showToast("Error saving run!", "error");
    }
  }

</script>

<main>
  {#if !loggedIn}
    <div class="login-card">
      <h1>ML Webview</h1>
      <div class="login-form">
        <input bind:value={username} placeholder="Username" />
        <input bind:value={password} placeholder="Password" />
        <button class="login-button" onclick={login}>Login</button>
      </div>
    </div>
  {:else}
    <div class="canvas-wrapper">
      {#if trainingInProgress && currentRunId == null}
        <p class="training-duration">{elapsedTime}</p>
      {/if}
      {#each canvasContainers as container, i}
        <canvas bind:this={canvasContainers[i]}></canvas>
      {/each}
    </div>
    <div class="controls">
      {#if trainingInProgress && currentRunId == null}
        <button class="control-button play-button" onclick={stopTraining} >
          <Square size="20" />
        </button>

      {:else if !trainingInProgress && currentRunId == null}
        <button class="control-button play-button" onclick={startTraining} >
          <Play size="20" />
        </button>
      {:else if currentRunId != null}
        <button class="control-button play-button" title="View Live Run" onclick={() => { currentRunId = null; }} >
          <Radio size="20" />
        </button>
      {/if}
      <button class="control-button" title="Download Chart" onclick={downloadChart}>
        <ImageDown size="20" />
      </button>
      <button class="control-button" title="Download CSV" onclick={downloadCSV}>
        <FileDown size="20" />
      </button>
      {#if currentRunId == null}
        <button class="control-button" title="Save Run" onclick={openSaveModal}>
          <HardDriveDownload size="20" />
        </button>
      {/if}
    </div>
    <div class="previous-runs">
      <h2>Previous Runs</h2>
      {#if previousRuns.length === 0}
        <p>No previous runs found.</p>
      {:else}
        <ul>
          {#each previousRuns as run}
            <li>
              <button class="run-item-button" onclick={() => { currentRunId = run.id; }} title="View Saved Run">
                <strong>{run.title}</strong> - {new Date(run.end_time).toLocaleString()}
                <p>{run.description}</p>
              </button>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
    {#if showSaveModal}
      <div class="modal-overlay">
        <div class="modal">
          <h2>Save Training Run</h2>
          <input bind:value={runTitle} placeholder="Run Title" />
          <textarea bind:value={runDescription} placeholder="Run Description"></textarea>
          <button onclick={() => { saveRun(); closeSaveModal(); fetchRuns();}}>Save</button>
          <button onclick={closeSaveModal}>Cancel</button>
        </div>
      </div>
    {/if}
  {/if}
  <Toasts />
</main>

<style>
  main {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: 2em;
    gap: 1.5em;
  }

  .login-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1.5em;
    padding: 4em;
    background-color: #333;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }
  
  input {
    padding: 0.5em;
    font-size: 1em;
    border-radius: 6px;
    border: none;
  }

  .login-form {
    display: flex;
    flex-direction: column;
    gap: 1em;
  }

  .login-button {
    padding: 0.5em;
    font-size: 1em;
    border-radius: 6px;
    border: none;
    background-color: #6366f1;
    color: white;
    cursor: pointer;
  }
  .login-button:hover {
    background-color: #535bf2;
  }

  .canvas-wrapper {
    width: 70%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background-color: hsl(0, 0%, 20%);
    border-radius: 20px;
  }

  .training-duration {
    color: white;
    margin-bottom: 0.5em;
    font-size: 1.2em;
  }

  canvas {
    width: 100%;
    aspect-ratio: 2 / 1;
    align-self: center;
    margin: 1em;
  }

  .controls {
    display: flex;
    align-items: center;
    /* gap: 1em; */
    width: 70%;
    background-color: hsl(0, 0%, 20%);
    border-radius: 20px;
  }

  .control-button {
    background-color: transparent;
    color: white;
    border: none;
    font-size: 3em;
    font-weight: 500;
    font-family: inherit;
    cursor: pointer;
    padding: 0.2em 0.5em;
    display: flex;
    align-items: left;
  }
  .control-button:hover {
    color: #646cff
  }

  .play-button {
    color: #646cff;
    border-bottom-left-radius: 20px;
    border-top-left-radius: 20px;
    border-right: 1px solid hsl(0, 0%, 13%);
  }
  .play-button:hover {
    background-color: #646cff;
    color: white;
  }

  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .modal {
    background-color: hsl(0, 0%, 20%);
    padding: 2em;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    gap: 1em;
    width: 300px;
  }

  .modal h2 {
    text-align: center;
  }

  .modal input, .modal textarea {
    padding: 0.5em;
    font-size: 1em;
    border-radius: 6px;
    border: 1px solid hsl(0, 0%, 40%);
  }

  .modal button {
    padding: 0.5em;
    font-size: 1em;
    border-radius: 6px;
    border: none;
    background-color: #6366f1;
    color: white;
    cursor: pointer;
  }

  .modal button:hover {
    background-color: #535bf2;
  }

  .previous-runs {
    width: 85%;
    background-color: hsl(0, 0%, 20%);
    border-radius: 20px;
    padding: 1em;
  }

  .previous-runs ul {
    list-style: none;
    padding: 0;
  }

  .previous-runs li {
    border-top: 1px solid hsl(0, 0%, 30%);
    padding: 0.5em 0;
  }

  .previous-runs strong {
    color: #646cff;
  }

  .previous-runs p {
    margin: 0.2em 0 0 0;
    color: hsl(0, 0%, 70%);
  }

  .run-item-button {
    background: none;
    border: none;
    width: 100%;
    text-align: left;
    padding: 0;
    margin: 0;
    color: inherit;
    font: inherit;
    cursor: pointer;
  }

  .run-item-button:hover {
    background: hsl(0, 0%, 25%);
    border-radius: 8px;
  }

  
</style>
