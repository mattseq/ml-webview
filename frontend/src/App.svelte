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
        alert("Login successful!");
        await tick();
        initSocket();
      } else {
        alert(data.message || "Login failed!");
      }
    } catch (err) {
      console.error("Login error:", err);
    }
  }

  async function startTraining() {
    const response = await fetch('/api/start', { method: 'POST', credentials: 'include' });
    if (response.ok) {
      trainingInProgress = true;
    } else {
      alert("Failed to start training!");
      return;
    }
  }
  function stopTraining() {
    fetch('/api/stop', { method: 'POST', credentials: 'include' });
    trainingInProgress = false;
  }
</script>

<main>
  {#if !loggedIn}
    <div class="login">
      <input bind:value={username} placeholder="Username" />
      <input bind:value={password} placeholder="Password" />
      <button onclick={login}>Login</button>
    </div>
  {:else}
    <canvas bind:this={canvasBind}></canvas>
    <div class="controls">
      {#if trainingInProgress}
        <p>Training in progress...</p>
        <button onclick={stopTraining} >
          <Square size="16" />
        </button>

      {:else}
        <p>Training not started.</p>
        <button onclick={startTraining} >
          <Play size="16" />
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
    padding: 2em;
    gap: 1.5em;
  }

  canvas {
    max-width: 800px;
    width: 100%;
    aspect-ratio: 2 / 1;
  }

  .controls {
    display: flex;
    align-items: center;
    gap: 1em;
  }

  button {
    background-color: transparent;
    color: #333;
    border: none;
    font-size: 3em;
    font-weight: 700;
    font-family: inherit;
    cursor: pointer;
    padding: 0px 0px;
  }
  button:hover {
    color: #646cff
  }
  
</style>
