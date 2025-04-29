// script.js

document.addEventListener("DOMContentLoaded", function() {
    const form = document.querySelector('form');
    const scrollToTopButton = document.getElementById("scrollToTop");

    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent the default form submission

            const formData = new FormData(form);
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                alert(data.message);
                // Redirect to the result page
                window.location.href = '/result'; // Redirect to the result page
            })
            .catch(error => {
                console.error('There was a problem with the fetch operation:', error);
            });
        });
    }

    // Smooth scroll to the top of the page
    if (scrollToTopButton) {
        scrollToTopButton.addEventListener("click", function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
});