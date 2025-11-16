<script>
  import { onMount, tick } from 'svelte';
  import Chart from 'chart.js/auto';
  import { io } from 'socket.io-client';
  import { Play, Square } from 'lucide-svelte';

  let chart;
  let canvasBind;
  let socket;

  let trainingInProgress = false;
  let loggedIn = false;

  let username = '';
  let password = '';

  onMount(() => {
    initialize();

    return () => {
      if (chart) {
        chart.destroy();
      }
      if (socket) {
        socket.disconnect();
      }
    };
  });

  async function initialize() {
    try {
      const res = await fetch('/api/status', { method: "GET", credentials: 'include' });
      const data = await res.json();
      loggedIn = data.loggedIn;
      if (loggedIn) {
        await tick();
        initSocket();
      }
    } catch (error) {
      console.error("Error checking login status:", error);
    }
  }

  function initSocket() {
    if (!canvasBind) return;
    
    const ctx = canvasBind.getContext('2d');
    chart = new Chart(ctx, {
      type: 'line',
      data: { labels: [], datasets: [{ label: 'Loss', data: [], borderColor: 'red', fill: false }] },
      options: {
          responsive: true,
          scales: {
              x: {
                  title: { display: true, text: 'Epoch' },
                  beginAtZero: true
              },
              y: {
                  title: { display: true, text: 'Loss' },
                  beginAtZero: true
              }
          }
      }
    });

    socket = io(window.location.origin);

    socket.on('status', (status) => {
      console.log("Status received:", status);
      trainingInProgress = status.training
    })

    socket.on('history', (history) => {
      console.log("History received:", history);

      history.forEach(data => {
          chart.data.labels.push(data.epoch);
          chart.data.datasets[0].data.push(data.loss);
      });

      chart.update();
    });

    socket.on('update', data => {
        console.log("Update received:", data);
        chart.data.labels.push(data.epoch);
        chart.data.datasets[0].data.push(data.loss);
        chart.update();
    });
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
        await tick();
        initSocket();
      } else {
        loggedIn = false;
        alert(data.message || "Login failed!");
      }
    } catch (err) {
      console.error("Login error:", err);
    }
  }

  async function startTraining() {
    const response = await fetch('/api/start', { method: 'POST', credentials: 'include' });
    if (!response.ok) {
      alert("Failed to start training!");
      return;
    }
  }
  async function stopTraining() {
    const response = await fetch('/api/stop', { method: 'POST', credentials: 'include' });
    if (!response.ok) {
      alert("Failed to stop training!");
      return;
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
      <canvas bind:this={canvasBind}></canvas>
    </div>
    <div class="controls">
      {#if trainingInProgress}
        <button class="control-button" onclick={stopTraining} >
          <Square size="20" />
        </button>

      {:else}
        <button class="control-button" onclick={startTraining} >
          <Play size="20" />
        </button>
      {/if}
    </div>
  {/if}
  
</main>

<style>
  main {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1.5em;
    height: 100%;
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
    justify-content: center;
    background-color: #333;
    padding: 1em;
    border-radius: 20px;
  }

  canvas {
    width: 100%;
    aspect-ratio: 2 / 1;
    align-self: center;
  }

  .controls {
    display: flex;
    align-items: center;
    gap: 1em;
    width: 70%;
    background-color: #333;
    padding: 1em;
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
    padding: 0px 5px;
    display: flex;
    align-items: left;
  }
  .control-button:hover {
    color: #646cff
  }
  
</style>
