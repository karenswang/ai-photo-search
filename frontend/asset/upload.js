var apigClient = apigClientFactory.newClient();

var selectedFile; // Variable to store the selected file
var base64Image; // Variable to store the base64-encoded image

function readImage(file) {
    if (file.type && !file.type.startsWith('image/')) {
        console.log('File is not an image.', file.type, file);
        return;
    }

    const reader = new FileReader();
    reader.addEventListener('load', (event) => {
        document.getElementById('imagePreview').src = event.target.result;
        base64Image = event.target.result; // Store the base64-encoded image
    });
    reader.readAsDataURL(file);
}

function handleUpload(event) {
    event.preventDefault();

    if (!selectedFile) {
        alert('Please select a file to upload first');
        return;
    }

    var customLabelsInput = document.getElementById('customLabelsInput');
    var customLabels = customLabelsInput.value || '';
    var objectKey = selectedFile.name;

    var params = {
        objectKey: objectKey,
        'x-amz-meta-customLabels': customLabels,
        'Content-Type': selectedFile.type
    };

    var additionalParams = {
        headers: {
            'Content-Type': selectedFile.type
        }
    };

    // // Use the base64Image data for upload
    // apigClient.uploadObjectKeyPut(params, base64Image, additionalParams)
    //     .then(function(response) {
    //         alert('File uploaded successfully');
    //     }).catch(function(error) {
    //         console.error('Upload error:', error);
    //         alert('Error during file upload. Please try again.');
    //     });
    // Read the file as binary data (Blob) and upload
    // const reader = new FileReader();
    // reader.addEventListener('load', (event) => {
    //     const result = event.target.result;
    //     apigClient.uploadObjectKeyPut(params, result, additionalParams)
    //         .then(function(response) {
    //             alert('File uploaded successfully');
    //         }).catch(function(error) {
    //             console.error('Upload error:', error);
    //             alert('Error during file upload. Please try again.');
    //         });
    // });
    // reader.readAsArrayBuffer(selectedFile);


    const reader = new FileReader();
    reader.addEventListener('load', (event) => {
      const result = event.target.result;
      apigClient.uploadObjectKeyPut(params, result, additionalParams)
      .then(function(response) {
          alert('File uploaded successfully');
      }).catch(function(error) {
          console.error('Upload error:', error);
          alert('Error during file upload. Please try again.');
      });
    });
  
    reader.addEventListener('progress', (event) => {
      if (event.loaded && event.total) {
        const percent = (event.loaded / event.total) * 100;
        console.log(`Progress: ${Math.round(percent)}`);
      }
    });
    reader.readAsDataURL(selectedFile);


    
  }
//     reader.onload = function (e) {
//         var binaryData = e.target.result;
//         console.log('Binary data:', binaryData);

//         apigClient.uploadObjectKeyPut(params, binaryData, additionalParams)
//             .then(function(response) {
//                 alert('File uploaded successfully');
//             }).catch(function(error) {
//                 console.error('Upload error:', error);
//                 alert('Error during file upload. Please try again.');
//             });
//     };
//     reader.readAsArrayBuffer(selectedFile);
// }

document.getElementById('photoInput').addEventListener('change', (event) => {
    selectedFile = event.target.files[0];
    readImage(selectedFile);
});

document.getElementById('uploadButton').addEventListener('click', handleUpload);
