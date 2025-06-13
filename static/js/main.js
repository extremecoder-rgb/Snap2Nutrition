document.addEventListener('DOMContentLoaded', function() {
    // Button triggers for the hidden file inputs
    document.getElementById('takePhotoBtn').addEventListener('click', function() {
        document.getElementById('cameraInput').click();
    });
    document.getElementById('uploadImageBtn').addEventListener('click', function() {
        document.getElementById('uploadInput').click();
    });

    // Handler for both camera and upload inputs
    function handleImageInput(e) {
        const file = e.target.files[0];
        if (!file) return;

        // Show preview
        const preview = document.getElementById('preview');
        const url = URL.createObjectURL(file);
        preview.src = url;
        preview.style.display = 'block';

        // Prepare and send to backend
        const formData = new FormData();
        formData.append('file', file);

        fetch('/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                // If the response is not OK (e.g., 400, 500 status code),
                // try to parse it as JSON first, then throw an error.
                return response.json().then(errData => {
                    throw new Error(errData.error || `Server error: ${response.status} ${response.statusText}`);
                }).catch(() => {
                    // If parsing as JSON fails, just throw a generic error.
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if(data.error) {
                alert('Error: ' + data.error);
                return;
            }
            document.getElementById('results').classList.remove('hidden');
            
            const totalCaloriesDiv = document.getElementById('totalCalories');
            const healthRatingDiv = document.getElementById('healthRating');
            const foodItemsDiv = document.getElementById('foodItems');
            const micronutrientsDiv = document.getElementById('micronutrients');

            console.log('totalCaloriesDiv:', totalCaloriesDiv);
            console.log('healthRatingDiv:', healthRatingDiv);
            console.log('foodItemsDiv:', foodItemsDiv);
            console.log('micronutrientsDiv:', micronutrientsDiv);

            // Clear previous results
            if (totalCaloriesDiv) totalCaloriesDiv.innerHTML = '';
            if (healthRatingDiv) healthRatingDiv.innerHTML = '';
            if (foodItemsDiv) foodItemsDiv.innerHTML = '';
            if (micronutrientsDiv) micronutrientsDiv.innerHTML = '';

            // Display Total Calories
            if (data.total_calories) {
                totalCaloriesDiv.innerHTML = `<h3>Total Calories:</h3> <p>${data.total_calories} kcal</p>`;
            }

            // Display Health Rating
            if (data.health_rating) {
                healthRatingDiv.innerHTML = `<h3>Health Rating:</h3> <p>${data.health_rating}</p>`;
            }

            // Display Food Items
            if (data.items && data.items.length > 0) {
                let itemsHtml = '<h3>Food Items:</h3>';
                data.items.forEach(item => {
                    itemsHtml += `
                        <div class="food-item-card">
                            <h4>${item.name || 'N/A'}</h4>
                            <p>Calories: ${item.calories || 'N/A'} kcal</p>
                            <p>Carbs: ${item.carbs || 'N/A'}g</p>
                            <p>Protein: ${item.protein || 'N/A'}g</p>
                            <p>Fat: ${item.fat || 'N/A'}g</p>
                            <p>Portion Size: ${item.portion_size || 'N/A'}</p>
                        </div>
                    `;
                });
                foodItemsDiv.innerHTML = itemsHtml;
            }

            // Display Micronutrients
            if (data.micronutrients) {
                let microHtml = '<h3>Micronutrients:</h3>';
                if (data.micronutrients.vitamins && data.micronutrients.vitamins.length > 0) {
                    const vitaminNames = data.micronutrients.vitamins.map(v => v.name || v);
                    microHtml += '<p><strong>Vitamins:</strong> ' + vitaminNames.join(', ') + '</p>';
                }
                if (data.micronutrients.minerals && data.micronutrients.minerals.length > 0) {
                    const mineralNames = data.micronutrients.minerals.map(m => m.name || m);
                    microHtml += '<p><strong>Minerals:</strong> ' + mineralNames.join(', ') + '</p>';
                }
                if (microHtml !== '<h3>Micronutrients:</h3>') { // Only display if there's actual content
                    micronutrientsDiv.innerHTML = microHtml;
                }
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            alert('Error: ' + error.message);
        });
    }

    document.getElementById('cameraInput').addEventListener('change', handleImageInput);
    document.getElementById('uploadInput').addEventListener('change', handleImageInput);
});
