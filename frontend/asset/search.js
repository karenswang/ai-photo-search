var apigClient = apigClientFactory.newClient();

// Function to handle text search
function handleTextSearch() {
    var keyword = document.getElementById('searchInput').value;
    if (!keyword) {
        alert('Please enter a search keyword');
        return;
    }
    searchPhotos(keyword);
}

// Function to handle voice search (Assuming transcribedText is passed from voice-to-text conversion logic)
function handleVoiceSearch(transcribedText) {
    searchPhotos(transcribedText);
}


// Voice search integration
if ('webkitSpeechRecognition' in window) {
    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    function startVoiceSearch() {
        console.log('start voice search'); 
        recognition.start(); // 
    }

    // Start voice search on microphone button click
    document.getElementById('micButton').addEventListener('click', startVoiceSearch);

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById('voiceResult').textContent = transcript;

        // Call your search API using the SDK
        handleVoiceSearch(transcript);


        // apigClient.searchGet({q: transcript}).then(function (response) {
        //     displaySearchResults(response.data);
        //         // Handle API response and display results
        //         // Update this part according to your API response structure
        //     }).catch(function (error) {
        //         console.error('API Call Error:', error);
        //     });
    };

    recognition.onerror = function (event) {
        console.error('Speech recognition error:', event.error);
    };
} else {
    alert('Your browser does not support the Web Speech API');
}





// Function to make the search API call
function searchPhotos(searchKeyword) {
    var params = {
        keyword: searchKeyword
    };
    var additionalParams = {
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': 'lzdREW8tNZHNWFDdoEp4KNmCwM4DVU5WtCTnhC40'
        }
    };

    apigClient.searchGet(params, {}, additionalParams)
        .then(function(response) {
            // Assuming the response format is as described
            var results = JSON.parse(response.data.body).results;
            displaySearchResults(results);
        }).catch(function(error) {
            console.error('Search error:', error);
            alert('Error during search. Please try again.');
        });
}

// Function to display search results
function displaySearchResults(data) {
    const resultsContainer = document.getElementById('results');
    
    resultsContainer.innerHTML = ''; // Clear existing results

    data.forEach(result => {
        var imgElement = document.createElement('img');
        imgElement.alt = 'Search result image';
        imgElement.className = 'result-image';
        // console.log('Bucket:', result.bucket, 'Object Key:', result.objectKey); // Debugging log
        presignedUrl = result.url;
        fetch(presignedUrl)
        .then(response => {
          if (response.ok) {
            return response.text(); // Use .json() if it's a JSON file
          }
          throw new Error('Network response was not ok.');
        })
        .then(data => {
          console.log(data); // Process the content
          imgElement.src = data;
        })
        .catch(error => {
          console.error('Fetch error:', error);
        });        


        var labelElement = document.createElement('p');
        labelElement.textContent = 'Labels: ' + result.labels.join(', ');

        var resultItem = document.createElement('div');
        resultItem.appendChild(imgElement);
        resultItem.appendChild(labelElement);

        resultsContainer.appendChild(resultItem);
    });
};

// Event listener for the search button
document.getElementById('searchButton').addEventListener('click', handleTextSearch);

// Add any necessary event listeners or logic for voice search integration
document.getElementById('micButton').addEventListener('click', startVoiceSearch);
