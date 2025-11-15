<script>
  import { onMount } from 'svelte';
  import Chart from 'chart.js/auto';
  import { io } from 'socket.io-client';
  import { Play, Square } from 'lucide-svelte';

  let chart;
  let canvasBind;
  let socket;

  let trainingInProgress = false;

  onMount(() => {
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

    return () => {
      if (chart) {
        chart.destroy();
      }
      if (socket) {
        socket.disconnect();
      }
    };
  });

  function startTraining() {
    fetch('/start');
    trainingInProgress = true;
  }
  function stopTraining() {
    fetch('/stop');
    trainingInProgress = false;
  }
</script>

<main>
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
    height: 70%;
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
