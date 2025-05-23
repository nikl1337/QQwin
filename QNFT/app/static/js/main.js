document.addEventListener('DOMContentLoaded', () => {
    // --- Common Helper Functions ---
    function updateStatus(elementId, message, isError = false, isLoading = false) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.className = ''; // Reset classes
            if (isError) element.classList.add('status-error');
            else if (isLoading) element.classList.add('status-loading');
            else if (message) element.classList.add('status-success');
        }
    }

    // --- Global variables to store state if needed across functions ---
    let currentFileId = null;
    let currentGeneratedGifPath = null; // Server path of the GIF
    let currentGeneratedGifUrl = null;  // URL to display the GIF

    // --- Price Fetching for Index Page ---
    async function fetchPricesForDisplay() {
        const btcElem = document.getElementById('btcPrice');
        const solElem = document.getElementById('solPrice');
        const tsElem = document.getElementById('timestamp');

        if (!btcElem || !solElem || !tsElem) return; // Only run on index page

        try {
            // Note: price_fetcher.py is a service, not directly exposed via Flask route yet.
            // For now, we'll simulate or assume these prices might come from another source
            // or that we'd need to add a route to expose get_btc_usdc_price and get_sol_usdc_price.
            // SIMULATING for now as direct service call from JS is not possible.
            // In a real setup, you'd fetch from an API endpoint that calls these services.
            // Let's assume we add a Flask route /api/current_prices that returns this.
            // For now, using placeholder values.
            
            // const response = await fetch('/api/current_prices'); // Hypothetical endpoint
            // if (!response.ok) throw new Error('Failed to fetch prices');
            // const prices = await response.json();
            // btcElem.textContent = `BTC/USDC: ${prices.btc_usdc || 'N/A'}`;
            // solElem.textContent = `SOL/USDC: ${prices.sol_usdc || 'N/A'}`;
            // tsElem.textContent = `Timestamp: ${new Date(prices.timestamp).toLocaleString()}`;
            
            // Placeholder implementation until an endpoint is made:
            btcElem.textContent = `BTC/USDC: Fetching... (dummy)`;
            solElem.textContent = `SOL/USDC: Fetching... (dummy)`;
            tsElem.textContent = `Timestamp: ${new Date().toLocaleString()}`;
            // Simulate a delay then update with dummy values
            setTimeout(() => {
                btcElem.textContent = `BTC/USDC: ${(Math.random() * 10000 + 50000).toFixed(2)} (dummy)`;
                solElem.textContent = `SOL/USDC: ${(Math.random() * 50 + 100).toFixed(2)} (dummy)`;
            }, 1000);

        } catch (error) {
            console.error('Error fetching prices:', error);
            if (btcElem) btcElem.textContent = 'BTC/USDC: Error';
            if (solElem) solElem.textContent = 'SOL/USDC: Error';
            if (tsElem) tsElem.textContent = `Timestamp: ${new Date().toLocaleString()}`;
        }
    }


    // --- Index Page Logic (Upload, GIF Gen, Mint) ---
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const imageFile = document.getElementById('imageUpload').files[0];
            const uploadStatusEl = 'uploadStatus';
            const gifGenStatusEl = 'gifGenerationStatus';
            const gifMintSection = document.getElementById('gifMintSection');
            const generatedGifImg = document.getElementById('generatedGif');

            if (!imageFile) {
                updateStatus(uploadStatusEl, 'Please select an image file.', true);
                return;
            }

            updateStatus(uploadStatusEl, 'Uploading image...', false, true);
            updateStatus(gifGenStatusEl, '');
            if (gifMintSection) gifMintSection.style.display = 'none';
            if (generatedGifImg) generatedGifImg.style.display = 'none';

            const formData = new FormData();
            formData.append('file', imageFile);

            try {
                const response = await fetch('/upload_image', { method: 'POST', body: formData });
                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    currentFileId = result.file_id;
                    updateStatus(uploadStatusEl, `Upload successful! File ID: ${currentFileId}. Generating GIF...`, false, false);
                    updateStatus(gifGenStatusEl, 'Generating GIF, please wait...', false, true);

                    // Now request GIF generation
                    const gifResponse = await fetch(`/generate_gif/${currentFileId}`);
                    const gifResult = await gifResponse.json();

                    if (gifResponse.ok && gifResult.status === 'success') {
                        currentGeneratedGifUrl = gifResult.gif_url; // e.g., /static/generated_gifs/final_xyz.gif
                        currentGeneratedGifPath = gifResult.gif_server_path; // e.g., QNFT/app/static/generated_gifs/final_xyz.gif
                        
                        updateStatus(gifGenStatusEl, 'GIF generated successfully!', false, false);
                        if (generatedGifImg) {
                            generatedGifImg.src = currentGeneratedGifUrl + '?t=' + new Date().getTime(); // Cache buster
                            generatedGifImg.style.display = 'block';
                        }
                        if (gifMintSection) gifMintSection.style.display = 'block';
                        fetchPricesForDisplay(); // Fetch prices when GIF is ready
                    } else {
                        throw new Error(gifResult.message || 'GIF generation failed.');
                    }
                } else {
                    throw new Error(result.message || 'Image upload failed.');
                }
            } catch (error) {
                console.error('Upload/GIF Error:', error);
                updateStatus(uploadStatusEl, `Error: ${error.message}`, true);
                updateStatus(gifGenStatusEl, '');
            }
        });
    }

    const mintNftButton = document.getElementById('mintNftButton');
    if (mintNftButton) {
        mintNftButton.addEventListener('click', async () => {
            const mintingStatusEl = 'mintingStatus';
            if (!currentFileId || !currentGeneratedGifPath) {
                updateStatus(mintingStatusEl, 'Error: No GIF available to mint.', true);
                return;
            }

            const mintType = document.querySelector('input[name="mintType"]:checked').value;
            const userDescription = document.getElementById('userDescription').value;

            updateStatus(mintingStatusEl, 'Minting NFT, please wait...', false, true);

            const payload = {
                image_id: currentFileId, // The original uploaded image ID
                gif_server_path: currentGeneratedGifPath, // Server path for the service
                mint_type: mintType,
                user_description: userDescription
            };

            try {
                const response = await fetch('/mint_nft', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    updateStatus(mintingStatusEl, `NFT Minted (Simulated)! Tx ID: ${result.transaction_id}. Metadata URI: ${result.metadata_uri}`, false, false);
                    // Optionally, clear form or redirect
                } else {
                     throw new Error(result.message || `Minting failed (HTTP ${response.status})`);
                }
            } catch (error) {
                console.error('Minting Error:', error);
                updateStatus(mintingStatusEl, `Error: ${error.message}`, true);
            }
        });
    }

    // --- Marketplace Page Logic ---
    const nftGrid = document.getElementById('nftGrid');
    if (nftGrid) {
        const marketplaceStatusEl = 'marketplaceStatus';
        updateStatus(marketplaceStatusEl, 'Loading NFTs...', false, true);
        fetch('/marketplace/nfts')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error ${response.status}`);
                return response.json();
            })
            .then(nfts => {
                updateStatus(marketplaceStatusEl, ''); // Clear loading message
                if (nfts && nfts.length > 0) {
                    nftGrid.innerHTML = ''; // Clear previous content
                    nfts.forEach(nft => {
                        const card = document.createElement('div');
                        card.className = 'nft-card';
                        card.innerHTML = `
                            <img src="${nft.gif_url}" alt="${nft.name}" onerror="this.src='/static/images/placeholder.png'; this.onerror=null;">
                            <h3>${nft.name}</h3>
                            <p><strong>ID:</strong> ${nft.id || 'N/A'}</p>
                            <p><strong>Mint Type:</strong> ${nft.mint_type || 'N/A'}</p>
                            <p><strong>Timestamp:</strong> ${nft.mint_timestamp_iso ? new Date(nft.mint_timestamp_iso).toLocaleString() : 'N/A'}</p>
                            <p><strong>BTC at Mint:</strong> ${nft.btc_price_at_mint !== undefined ? nft.btc_price_at_mint : 'N/A'}</p>
                            <p><strong>SOL at Mint:</strong> ${nft.sol_price_at_mint !== undefined ? nft.sol_price_at_mint : 'N/A'}</p>
                            ${nft.original_image_url ? `<p><a href="${nft.original_image_url}" target="_blank">View Original Image</a></p>` : ''}
                        `;
                        nftGrid.appendChild(card);
                    });
                } else {
                    updateStatus(marketplaceStatusEl, 'No NFTs found in the marketplace yet.', false, false);
                }
            })
            .catch(error => {
                console.error('Error fetching marketplace NFTs:', error);
                updateStatus(marketplaceStatusEl, `Error fetching NFTs: ${error.message}`, true);
            });
    }

    // --- Price Chart Page Logic ---
    const priceChartCanvas = document.getElementById('priceChartCanvas');
    let currentChartInstance = null; // To manage chart updates

    async function fetchAndRenderChart(timeRangeHours) {
        const chartStatusEl = 'chartStatus';
        if (!priceChartCanvas) return;

        // TODO: Fetch BTC/USDC data and allow switching or displaying alongside SOL/USDC.
        updateStatus(chartStatusEl, `Loading chart data for ${timeRangeHours}h...`, false, true);

        try {
            const response = await fetch(`/chart/price_data?time_range_hours=${timeRangeHours}`);
            if (!response.ok) throw new Error(`HTTP error ${response.status}`);
            const data = await response.json();
            updateStatus(chartStatusEl, ''); // Clear loading

            if (currentChartInstance) {
                currentChartInstance.destroy(); // Destroy previous chart instance
            }

            const ctx = priceChartCanvas.getContext('2d');
            currentChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    // labels: data.price_history.map(p => new Date(p[0]).toLocaleTimeString()), // Simpler labels
                    datasets: [{
                        label: 'SOL/USDC Price',
                        data: data.price_history.map(p => ({ x: p[0], y: p[1] })),
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1,
                        pointRadius: data.price_history.length < 100 ? 3 : 0, // Show points if not too many
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'hour',
                                tooltipFormat: 'MMM d, yyyy HH:mm',
                                displayFormats: {
                                    hour: 'HH:mm'
                                }
                            },
                            title: { display: true, text: 'Time' }
                        },
                        y: {
                            title: { display: true, text: 'Price (USDC)' },
                            beginAtZero: false
                        }
                    },
                    plugins: {
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                        },
                        annotation: { // For NFT events
                            annotations: data.nft_events.map(event => ({
                                type: 'point',
                                xValue: event.timestamp,
                                yValue: event.sol_price_at_mint, // Plot on the price line at mint time
                                backgroundColor: event.type === 'long' ? 'rgba(0, 255, 0, 0.7)' : 'rgba(255, 0, 0, 0.7)',
                                radius: 7,
                                pointStyle: event.type === 'long' ? 'triangle' : 'rectRot', // up triangle for long, diamond for short
                                rotation: event.type === 'long' ? 0 : 45, 
                                // Custom tooltip for annotations (might require more specific Chart.js v3/v4 setup)
                                callout: {
                                    enabled: true,
                                    content: `${event.nft_name} (${event.type})`,
                                    yAdjust: -10
                                }
                                // For Chart.js v2, you might need a different approach for tooltips on annotations or draw custom points
                            }))
                        }
                    }
                }
            });
             // If using chartjs-plugin-annotation, it usually auto-registers.
             // If not, Chart.register(ChartAnnotation); might be needed if using an older version or specific bundle.
        } catch (error) {
            console.error('Error fetching or rendering chart data:', error);
            updateStatus(chartStatusEl, `Error loading chart: ${error.message}`, true);
        }
    }

    const timeRangeSelect = document.getElementById('timeRange');
    if (timeRangeSelect && priceChartCanvas) {
        timeRangeSelect.addEventListener('change', (event) => {
            fetchAndRenderChart(parseInt(event.target.value));
        });
        // Initial load
        fetchAndRenderChart(parseInt(timeRangeSelect.value));
    }

}); // End DOMContentLoaded
