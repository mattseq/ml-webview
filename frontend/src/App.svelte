<script>
  import { onMount } from 'svelte';
  import Chart from 'chart.js/auto';
  import { io } from 'socket.io-client';

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

  {#if trainingInProgress}
    <p>Training in progress...</p>
    <button onclick={stopTraining} >Stop Training</button>
  {:else}
    <p>Training not started.</p>
    <button onclick={startTraining} >Start Training</button>
  {/if}
</main>

<style>
  canvas {
    max-width: 800px;
    max-height: 600px;
    width: 100%;
    height: auto;
  }

  main {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
  }

  button {
    position: absolute;
    top: 20px;
    right: 20px;
    padding: 10px 20px;
    font-size: 16px;
    cursor: pointer;
  }
</style>
