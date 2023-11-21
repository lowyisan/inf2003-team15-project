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

function displayResults(data) {
    const resultsContainer = document.querySelector('.results-container');
    resultsContainer.innerHTML = ''; // Clear previous results
    data.forEach(agent => {
        const agentElement = document.createElement('div');
        let reviewsContent = '';

        // Iterate over each review and format it
        agent.reviews.forEach(review => {
            reviewsContent += `<p><strong>Rating:</strong> ${review.rating} / 5<br>${review.content}</p>`;
        });

        // Include CEANumber and agencyLicenseNo outside the reviews loop
        agentElement.innerHTML = 
        `<div class="container-xxl py-5">
            <div class="container">
                <div class="text-center mx-auto mb-5 wow fadeInUp" data-wow-delay="0.1s" style="max-width: 600px;">
                    <h1 class="mb-3">${agent.agentName}</h1>
                    <p><strong>CEANumber:</strong> ${agent.CEANumber}</p>
                    <p><strong>Agency License No:</strong> ${agent.agencyLicenseNo}</p>
                    <p>${reviewsContent}</p>
                </div>
            </div>
        </div>`;
        resultsContainer.appendChild(agentElement);
    });
}

