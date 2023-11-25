document.addEventListener('DOMContentLoaded', function () {
    document.querySelector('#btn-search').addEventListener('click', function () {
        var searchText = document.querySelector('#input-search').value;

        fetch('/search_agents?query=' + searchText)
            .then(response => response.json())
            .then(data => {
                displayResults(data);
                console.log("hello");
            })
            .catch(error => {
                console.error('Error:', error);
                showBubbleMessage('An error occurred.', 'error');
            });
    });
});

// JavaScript code for displaying search results
function displayResults(data) {
    const resultsContainer = document.querySelector('.results-container');
    resultsContainer.innerHTML = ''; // Clear previous results
    data.forEach(agent => {
        const agentElement = document.createElement('div');
        let reviewsContent = '';
        resultsContainer.appendChild(agentElement);
        currentAgent = agent.agentName; // Update the currentAgent variable

        agent.reviews.forEach((review, index) => {
            reviewsContent += `
                <p>
                    <strong>Rating:</strong> ${review.rating} / 5<br>
                    ${review.content}
                    <button onclick="showUpdateReviewForm('${agent.agentName}', '${review.content}')">Update</button>
                    <button onclick="deleteReview('${agent.agentName}', '${review.content}', ${review.rating})">Delete</button>
                </p>`;
        });

        // Include CEANumber, agencyLicenseNo, and averageRating outside the reviews loop
        agentElement.innerHTML =
            `<div class="container-xxl py-5">
            <div class="container">
                <div class="text-center mx-auto mb-5 wow fadeInUp" data-wow-delay="0.1s" style="max-width: 600px;">
                    <h1 class="mb-3">${agent.agentName}</h1>
                    <p><strong>CEANumber:</strong> ${agent.CEANumber}</p>
                    <p><strong>Agency License No:</strong> ${agent.agencyLicenseNo}</p>
                    <p><strong>Average Rating:</strong> ${agent.averageRating.toFixed(2)}</p>
                    <p>${reviewsContent}</p>
                </div>
            </div>
        </div>`;
        resultsContainer.appendChild(agentElement);
    });
    if (data.length > 0) {
        // Set the hidden agentName field's value
        document.getElementById('agent-name').value = currentAgent;

        // Change the display style of the review form to make it visible
        document.querySelector('#review-form').style.display = 'block';
    }

    // Display the average rating section if there are results with average ratings
    const averageRatingSection = document.getElementById('average-rating-section');
    const averageRatingParagraph = document.getElementById('average-rating');
    const hasAverageRatings = data.some(agent => agent.averageRating !== null);

    if (hasAverageRatings) {
        const averageRatings = data.map(agent => agent.averageRating).filter(avg => avg !== null);
        const totalAverageRating = averageRatings.reduce((sum, avg) => sum + avg, 0) / averageRatings.length;
        averageRatingParagraph.textContent = `Average Rating: ${totalAverageRating.toFixed(2)}`;
        averageRatingSection.style.display = 'block';
    } else {
        averageRatingSection.style.display = 'none';
    }
}


function deleteReview(agentName, reviewContent, reviewRating) {
    fetch(`/delete_review?agentName=${encodeURIComponent(agentName)}&reviewContent=${encodeURIComponent(reviewContent)}&reviewRating=${reviewRating}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            // Refresh the displayed reviews or handle UI updates here
        })
        .catch(error => console.error('Error:', error));
}

function showUpdateReviewForm(agentName, reviewContent) {
    // Fill in the agent name and review content in the update form
    document.getElementById('update-agent-name').value = agentName;
    document.getElementById('update-review-content').value = reviewContent;

    // Display the update form
    document.querySelector('#update-review-form').style.display = 'block';
}